from patterns import (
    Parameter,
    State,
    Table,
)
import json
import requests

most_relevant_records = Table("most_relevant_records", "r")
records = most_relevant_records.read()

errors = []
if len(records) > 0:
    application_id = records[0]['application_id']
    interaction_token = records[0]['interaction_token']
    search_text = records[0]['search_text']
    url = f'https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}/messages/@original'

    json_response = {
        "content": f"Here are the 5 most relevant results to '{search_text}'",
        'embeds': []
    }
    for idx, record in enumerate(records):
        # https://github.com/AnIdiotsGuide/discordjs-bot-guide/blob/master/first-bot/using-embeds-in-messages.md
        if record['type'] == 'discord':
            json_response['embeds'].append(
                {
                    'color': 15105570,
                    'type': 'link',
                    'author': json.loads(record['author']),
                    'title': f"Discord message: {record['content'][:230]}",
                    'url': f"https://discord.com/channels/{record['guild_id']}/{record['channel_id']}/{record['id']}",
                }
            )
        elif record['type'] == 'docs':
            json_response['embeds'].append(
                {
                    'color': 5763719,
                    'type': 'link',
                    # 'author': json.loads(record['author']),
                    'title': f"Docs page: {record['url']}",
                    'url': record['url'],
                }
            )
        elif record['type'] == 'issues':
            json_response['embeds'].append(
                {
                    'color': 15548997,
                    'type': 'link',
                    'title': f"Github Issue page: {record['title']}",
                    'url': record['html_url'],
                }
            )

    r = requests.patch(url, headers={}, json=json_response)

    if r.status_code != 200:
        errors.append(r.text)
    print(r.text)
    
if len(errors) > 0:
    raise Exception(', '.join(errors))
