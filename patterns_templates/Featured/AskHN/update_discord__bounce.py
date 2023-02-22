from patterns import (
    Parameter,
    State,
    Table,
)
import json
import requests


messages = Table("bounces", "r")


for record in messages.as_stream():
    msg = record["record"]
    application_id = msg['application_id']
    interaction_token = msg['token']
    question = msg["data"]
    url = f'https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}/messages/@original'
    json_response = {
        "content": f"Thanks for your question, I'm all jammed up with requests, please wait 15s or so and try again!",
        'embeds': []
    }
    r = requests.patch(url, headers={}, json=json_response)

    print(r.status_code)
    print(r.text)

