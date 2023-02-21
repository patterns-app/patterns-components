from patterns import (
    Parameter,
    State,
    Table,
)
import json
import requests


messages = Table("discord_messages_filtered", "r")


for record in messages.as_stream():
    msg = record["record"]
    application_id = msg['application_id']
    interaction_token = msg['token']
    question = record["question"]
    url = f'https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}/messages/@original'
    json_response = {
        "content": f"Thanks for your question `{question}` -- working on it, gimme a few secs",
        'embeds': []
    }
    r = requests.patch(url, headers={}, json=json_response)

    print(r.status_code)
    print(r.text)

