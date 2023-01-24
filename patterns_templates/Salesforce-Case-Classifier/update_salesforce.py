from patterns import (
    Parameter,
    State,
    Table,
    Connection
)

import requests
import json

salesforce = Parameter(
    'salesforce',
    type=Connection("salesforce")
)

access_token = salesforce.get("access_token")
instance_url = salesforce.get("instance_url")

cases = Table('cohere_output')
cases_stream = cases.as_stream()

headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

for c in cases_stream.consume_records():
    case_id=c['Id']
    prediction=c['prediction']
    data={ "Type": c['prediction'] }

    result = requests.patch(
        url=f'{instance_url}/services/data/v56.0/sobjects/Case/{case_id}',
        data=json.dumps(data),
        headers=headers
    )

    result.raise_for_status()