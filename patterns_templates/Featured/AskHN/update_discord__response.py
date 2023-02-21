from patterns import (
    Parameter,
    State,
    Table,
)
import json
import requests


messages = Table("responses", "r")


for record in messages.as_stream():
    msg = record["record"]
    application_id = msg['application_id']
    interaction_token = msg['token']
    url = f'https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}/messages/@original'
    json_response = {
        "content": record["response"],
        'embeds': []
    }
    r = requests.patch(url, headers={}, json=json_response)

    print(r.status_code)
    print(r.text)

