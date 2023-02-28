from patterns import (
    Parameter,
    State,
    Table,
)

import requests

channel_table = Table("channel_table", "w")

discord_server_id = Parameter("discord_server_id", type=str )
discord_bot_token = Parameter("discord_bot_token", type=str )

url = f"https://discord.com/api/v10/guilds/{discord_server_id}/channels"
headers = {"Authorization": f"Bot {discord_bot_token}"}

r = requests.get(url, headers=headers)

data = r.json()

channel_table.init(schema_hints={'id': "Text"})

channel_table.reset()
for channel in data:
    channel_table.append(channel)

