from fastapi import FastAPI, BackgroundTasks
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

canBeGrouped = False
data = None # This will be used to store the data from the scraper task. Normally database logic will be implemented here.

@app.get("/")
def read_root():
    return {"Information": "Welcome to the GlassDollar Scraper API. You can start scraping by going to /scraper. After scraping process is done you can go to /grouper to group the companies according to the closeness criteria."}

@app.get("/scraper")
async def scraper():
    global scraping, scraperId, canBeGrouped, data

    # Code to start the Celery tasks
    if not scraping:

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
    
    elif scraping and not canBeGrouped:
        # Restore the GroupResult object using the saved ID
        details_result = GroupResult.restore(scraperId, app=celery_app)

        if not details_result or not details_result.ready():
            return {"status": "Scraping is still in progress"} # Assumed no error is happened
        
        # data = [result.get() for result in group_result.children]
        data = details_result.get()
        print_schema(data)
        scraping = False
        canBeGrouped = True

        with open('company_details.json', 'w') as file:
            file.write(json.dumps(data, indent=4))

        return JSONResponse(content={"status": "Scraping completed. Scraping results added to a company_details.json. You can now group them from /grouper .", "Count of the companies" : len(data), "results": data}, media_type="application/json")
    
    else:
        scraping = False
        canBeGrouped = False
        return {"status": "I dont know how did this aciton triggered? I resetted all. Please restart again"}
    
@app.get("/grouper")
async def group_companies(): # background_tasks is used to run the task in the background then discarded because of the time of the task is short.
    global scraping, canBeGrouped, data
    
    if scraping:
        return {"status": "Scraping is still in progress. You can not group the results yet. You need to go to /scraper first and wait it to be completed."}

    elif not canBeGrouped:
        return {"status": "You need to go to /scraper first to start scraping."}
    
    elif canBeGrouped:
        
        companies, num_clusters = grouper(data)
        
        clusters = {}
        for i in range(1, num_clusters + 1):
            clusters[f'Cluster {i}'] = [(company['name'] , company['id']) for company in companies if company['clusterNo'] == i]

        with open('clusters.json', 'w') as file:
            json.dump(clusters, file, indent=4)

        canBeGrouped = False

        
        with open('company_details.json', 'w') as file:
            file.write(json.dumps(data, indent=4))

        return JSONResponse(content={"status": "Grouping completed. Grouped results added to a clusters.json. Additionally company_details.json is updated with new field clusterNo if you want to get more info.", "Cluster count": num_clusters  , "Cluster results": clusters}, media_type="application/json")

