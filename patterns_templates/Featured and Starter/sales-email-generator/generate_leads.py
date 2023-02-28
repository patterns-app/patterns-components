from patterns import (
    Parameter,
    State,
    Table,
    Connection,
)

from time import sleep
import requests, json, csv

connection = Parameter(
    "connection",
    type=Connection("peopledatalabs"),
    description="People Data Labs Connection",
)

query_str = Parameter(
    "company_query",
    type=str,
    default="""{
        "bool": {
            "must": [
                {"term": {"industry": "computer software"}},
                {"range": {"employee_count": { "gt": 1000 }}}
            ]
        }
    }""",
    description="The PDL query as JSON. Documentation here: https://docs.peopledatalabs.com/docs/input-parameters-person-search-api"
)

out_table = Table("leads", "w")

API_KEY = connection.get("api_key")

PDL_COMPANY_SEARCH_URL = "https://api.peopledatalabs.com/v5/company/search"
PDL_PERSON_SEARCH_URL = "https://api.peopledatalabs.com/v5/person/search"

all_records = []

HEADERS = {
    'Content-Type': "application/json",
    'X-api-key': API_KEY
}

ES_QUERY = {
    "query": json.loads(query_str)
}

PARAMS = {
    'query': json.dumps(ES_QUERY),
    'size': 10
}

response = requests.get(
    PDL_COMPANY_SEARCH_URL,
    headers = HEADERS,
    params = PARAMS
).json()

if response["status"] == 200:
    data = response['data']
    for record in data:
        ES_QUERY = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"job_company_id": record['id']}},
                        {"term": {"job_title_levels": "director"}},
                        {"term": {"job_title_role": "engineering"}},
                    ]
                }
            }
        }
        PARAMS = {
            'query': json.dumps(ES_QUERY),
            'size': 1
        }
        response = requests.get(
            PDL_PERSON_SEARCH_URL,
            headers = HEADERS,
            params = PARAMS
        ).json()
        
        if response["status"] == 200:
            data = response['data']
            all_records.extend(data)
        else:
            print("Person Search Error:", response)
else:
    print("Company Search Error:", response)

out_table.reset()
out_table.write(all_records)