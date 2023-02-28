from patterns import (
    Parameter,
    State,
    Table,
)
import json
import requests

webhook = Table("webhook", "r")
search_text_table = Table("search_text", "w")

stream = webhook.as_stream()

for record in stream.consume_records():
    application_id = record['record']['application_id']
    interaction_token = record['record']['token']
    search_text = record['record']['data']['options'][0]['value']

    search_text_table.append({
        'application_id': application_id, 
        'interaction_token': interaction_token, 
        'search_text': search_text 
    })




