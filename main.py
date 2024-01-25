from fastapi import FastAPI
from fastapi.responses import JSONResponse
from print_schema import print_schema
from celery import group, chain
from celery.result import GroupResult

import requests
import json

from tasks import fetch_company_details, fetch_all_companies
from tasks import app as celery_app
from closeness import grouper

app = FastAPI()

scraping = False
scraperId = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/scraper")
async def scraper():
    global scraping, scraperId

    # Code to start the Celery tasks
    if not scraping:
        print("Scaping started")

        # Creating a group of tasks for fetching companies on each page
        fetch_tasks = group(fetch_all_companies.s(page) for page in range(1, 28))

        # Executing the group asynchronously and storing the group result
        group_result = fetch_tasks.apply_async()
        group_result.save()


        # Waiting for all fetch_all_companies tasks to complete
        all_companies = []
        for async_result in group_result.get():
            if async_result:
                all_companies.extend(async_result)

        # Queue tasks for each company ID using Celery
        detail_tasks = [fetch_company_details.s(company['id']) for company in all_companies]
        details_job = group(detail_tasks)
        details_result = details_job.apply_async(countdown=0)
        details_result.save()
        scraping = True
        scraperId = details_result.id


        # status = fetch_company_details.AsyncResult(result.id).status
        return {"status": "Scraping started, please come back later for results."}
    
    else:
        # Restore the GroupResult object using the saved ID
        details_result = GroupResult.restore(scraperId, app=celery_app)

        if not details_result or not details_result.ready():
            return {"status": "Scraping is still in progress"} # Assumed no error is happened
        
        scraping = False
        # details_results = [result.get() for result in group_result.children]
        details_results = details_result.get()
        print_schema(details_results)
        names = [company.get('name') for company in details_results if company and 'twitter_url' in company]
        
        
        companies, num_clusters = grouper(details_results)

     
        clustered_companies = {}
        for i in range(1, num_clusters + 1):
            clustered_companies[f'Cluster {i}'] = [company['name'] for company in companies if company['cluster'] == i]

        with open('clustered_companies.json', 'w') as file:
            json.dump(clustered_companies, file, indent=4)

        with open('company_details.json', 'w') as file:
            file.write(json.dumps(details_results, indent=4))

        
        print("Scraping completed")
        return JSONResponse(content={"status": "All tasks completed", "results": details_results}, media_type="application/json")
