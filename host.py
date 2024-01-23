from tasks import fetch_company_details  
import requests
import json
from celery import group
from print_schema import print_schema

# Headers for the requests
headers = {
    'accept': '*/*',
    'accept-language': 'tr-TR,tr;q=0.6',
    'content-type': 'application/json',
    'origin': 'https://ranking.glassdollar.com',
    'referer': 'https://ranking.glassdollar.com/',
}

first_request_data = {
    'operationName': 'TopRankedCorporates',
    'variables': {},
    'query': 'query TopRankedCorporates {\n  topRankedCorporates {\n    id\n    name\n    logo_url\n    industry\n    hq_city\n    startup_partners {\n      company_name\n      logo_url: logo\n      __typename\n    }\n    startup_friendly_badge\n    __typename\n  }\n}\n',
}


# response = requests.post('https://ranking.glassdollar.com/graphql', headers=headers, json=first_request_data)
# top_companies = response.json()['data']['topRankedCorporates']

# print(len(top_companies))


# # Queue tasks for each company ID using Celery
# tasks = [fetch_company_details.s(company['id']) for company in top_companies]
# job = group(tasks)  # group the tasks to be executed in parallel
# result = job.apply_async()  # apply_async will send the tasks to the workers

# # Optional: Wait for all tasks to finish and collect the results
# company_details = result.join()  # This will block until all tasks are done

# # Format the data into JSON
# formatted_data = json.dumps(company_details, indent=4)
# # You can print or save the formatted data as needed

# print(len(company_details))
# print_schema(company_details, indent=3, dense=False)


# with open('company_details.json', 'w') as file:
#     file.write(formatted_data)