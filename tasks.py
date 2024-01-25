import requests
import json
from celery import Celery, chord
from celery.utils.log import get_task_logger

# app = Celery('CompanyAnalyzer', broker='pyamqp://guest@localhost//', backend='redis://localhost')


app = Celery('CompanyAnalyzer', 
             broker='pyamqp://guest:guest@rabbitmq:5672//', 
             backend='redis://redis:6379/0')


logger = get_task_logger(__name__)

@app.task(name='tasks.fetch_company_details_tester')
def fetch_company_details_tester(company_id):
    print(company_id, "is being processed")	
    logger.info(f"{company_id} is being processed")
    return company_id

@app.task(name='tasks.fetch_company_details')
def fetch_company_details(company_id):
    headerDetailed = {
        'accept': '*/*',
        'accept-language': 'tr-TR,tr;q=0.6',
        'content-type': 'application/json',
        'origin': 'https://ranking.glassdollar.com',
        'referer': f'https://ranking.glassdollar.com/corporates/{company_id}',
    }
        
    json_data = {
        'variables': {
            'id': company_id,
        },
        'query': 'query ($id: String!) {\n  corporate(id: $id) {\n    id\n    name\n    description\n    logo_url\n    hq_city\n    hq_country\n    website_url\n    linkedin_url\n    twitter_url\n    startup_partners_count\n    startup_partners {\n      master_startup_id\n      company_name\n      logo_url: logo\n      city\n      website\n      country\n      theme_gd\n     }\n    startup_themes\n    }\n}\n',
    }

    try:
        # Your code to fetch company details
        response = requests.post('https://ranking.glassdollar.com/graphql', headers=headerDetailed, json=json_data)
        return response.json()['data']['corporate']
    except Exception as exc:
        raise "Excessive amount of requests to the server. Please try again later."
        



@app.task(name='tasks.fetch_all_companies')
def fetch_all_companies(pageNo):
    headers = {
        'accept': '*/*',
        'accept-language': 'tr-TR,tr;q=0.6',
        'content-type': 'application/json',
        'origin': 'https://ranking.glassdollar.com',
        'referer': 'https://ranking.glassdollar.com/',
    }
    
    json_data = {
        'query': 'query GetCorporates($page: Int, $filters: CorporateFilters, $sortBy: String) {\n  corporates(page: $page, filters: $filters, sortBy: $sortBy) {\n    rows {\n      id\n     }\n  }\n}\n',
        'variables': {
            'page': pageNo, 
            'filters': {
                'hq_city': [],
                'industry': [],
            },
            'sortBy': '',
        },
    }
    
    response = requests.post('https://ranking.glassdollar.com/graphql', headers=headers, json=json_data)
    return response.json()['data']['corporates']['rows']
