from patterns import (
    Parameter,
    State,
    Table,
)

import requests


discord_app_id = Parameter("discord_app_id", type=str )
discord_bot_token = Parameter("discord_bot_token", type=str )


url = f"https://discord.com/api/v10/applications/{discord_app_id}/commands"



# This is an example CHAT_INPUT or Slash Command, with a type of 1
json = {
    "name": "askhn",
    "type": 1,
    "description": "Ask HN",
    "options": [
        {
            "name": "question",
            "description": "Ask HN ",
            "type": 3,
            "required": True,
        },
    ]
}

headers = {"Authorization": f"Bot {discord_bot_token}"}



r = requests.post(url, headers=headers, json=json)

print(r.status_code)
print(r.text)
