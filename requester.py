import requests
import json
from celery import Celery
from celery.utils.log import get_task_logger

app = Celery('CompanyAnalyzer', broker='pyamqp://guest@localhost//')
app.conf.result_backend = 'rpc://'

logger = get_task_logger(__name__)

@app.task(name='requester.fetch_company_details_tester')
def fetch_company_details_tester(company_id):
    print(company_id, "is being processed")	
    logger.info(f"{company_id} is being processed")
    return company_id

@app.task(name='requester.fetch_company_details')
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
        'query': 'query ($id: String!) {\n  corporate(id: $id) {\n    id\n    name\n    description\n    logo_url\n    hq_city\n    hq_country\n    website_url\n    linkedin_url\n    twitter_url\n    startup_partners_count\n    startup_partners {\n      master_startup_id\n      company_name\n      logo_url: logo\n      city\n      website\n      country\n      theme_gd\n      __typename\n    }\n    startup_themes\n    startup_friendly_badge\n    __typename\n  }\n}\n',
    }
    response = requests.post('https://ranking.glassdollar.com/graphql', headers=headerDetailed, json=json_data)
    return response.json()['data']['corporate']


# # Printing or saving the formatted data
# print(formatted_data)
# # Optionally, you can save the data to a file
# with open('company_details.json', 'w') as file:
#     file.write(formatted_data)

