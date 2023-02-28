from patterns import (
    Parameter,
    State,
    Table,
)
import requests
import json
import time 

channel_table = Table("channel_table", "r")

messages_table = Table("messages_table", "w")
discord_bot_token = Parameter("discord_bot_token", type=str )

headers = {"Authorization": f"Bot {discord_bot_token}"}

messages_table.reset()

messages_with_content = []

for channel_record in channel_table.read():
    channel_id = channel_record['id']
    read_all_messages = False
    last_message_id = None
    while not read_all_messages:
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=100"
        print(url)
        if last_message_id:
            url += f"&before={last_message_id}"

        r = requests.get(url, headers=headers)
        data = r.json()

        print(data)

        for message in data:
            print(type(message), message)
            content = message.get('content', '')
            if len(content) > 0:
                message['guild_id'] = channel_record['guild_id']
                messages_table.append(message)

        if len(data) < 100:
            read_all_messages = True
        else:
            last_message_id = data[-1]['id']
            time.sleep(1)

        

