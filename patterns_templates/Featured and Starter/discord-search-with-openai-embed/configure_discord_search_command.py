from patterns import (
    Parameter,
    State,
    Table,
)

import requests

application_id = Parameter('application_id', type=str)


url = f"https://discord.com/api/v10/applications/{application_id}/commands"

discord_bot_token = Parameter("discord_bot_token", type=str )

# This is an example CHAT_INPUT or Slash Command, with a type of 1
json = {
    "name": "search",
    "type": 1,
    "description": "Search previous messages",
    "options": [
        {
            "name": "search_text",
            "description": "The search text to search for ",
            "type": 3,
            "required": True,
        },
    ]
}

headers = {"Authorization": f"Bot {discord_bot_token}"}

r = requests.post(url, headers=headers, json=json)

if r.status_code != 200:
    raise Exception(r.text)
print(r.text)
