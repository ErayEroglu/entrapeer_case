from fastapi import FastAPI
from tasks import fetch_company_details  
import requests
import json
from celery import group
from print_schema import print_schema
from celery.result import GroupResult
from tasks import app as celery_app
from fastapi.responses import JSONResponse

import io
import sys
def capture_print_schema_to_html(data):
    # Capture the output as before
    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer
    print_schema(data)
    sys.stdout = old_stdout
    content = buffer.getvalue()
    buffer.close()

    # # Convert the captured output to HTML
    # html_content = content.replace('\n', '<br>').replace('\t', '&nbsp;' * 4)
    return content

from host import headers, first_request_data

app = FastAPI()

scraping = False
status = None
scraperId = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/scraper")
async def scraper():
    global scraping, scraperId

    # Code to start the Celery tasks
    if not scraping:
        response = requests.post('https://ranking.glassdollar.com/graphql', headers=headers, json=first_request_data)
        top_companies = response.json()['data']['topRankedCorporates']
        print("Scaping started")

        # Queue tasks for each company ID using Celery
        tasks = [fetch_company_details.s(company['id']) for company in top_companies]
        job = group(tasks)  # group the tasks to be executed in parallel
        result = job.apply_async(countdown=2)  # apply_async will send the tasks to the workers
        result.save()
        scraping = True
        scraperId = result.id
        # status = fetch_company_details.AsyncResult(result.id).status
        return {"status": "Scraping started, please come back later for results."}
    
    else:
        # Restore the GroupResult object using the saved ID
        group_result = GroupResult.restore(scraperId, app=celery_app)

        if not group_result:
            return {"status": "Invalid job ID or job may have expired"}

        # Check if all tasks in the group are completed
        if group_result.ready():
            scraping = False
            # Retrieve the results of all tasks
            results = group_result.get()
            # Optionally, you can format the results as JSON
            formatted_results = json.dumps(results, indent=4)
            # Print the results (or return them in the response)
            print_schema(results)

            return {"status": "All tasks completed", "results len": len(results) }
        else:
            return {"status": "Tasks still running"}




# # # Optional: Wait for all tasks to finish and collect the results
# # company_details = result.join()  # This will block until all tasks are done

# # Format the data into JSON
# formatted_data = json.dumps(company_details, indent=4)
# # You can print or save the formatted data as needed

# print(len(company_details))
# print_schema(company_details, indent=3, dense=False)