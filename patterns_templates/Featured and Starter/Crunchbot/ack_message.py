from patterns import (
    Parameter,
    State,
    Table,
    Connection,
)
import requests
import random
from patterns_components.helpers.api import handle_rate_limiting

responses = Table("questions")
slack_connection = Parameter("slackbot_connection", type=Connection("slackbot"))


for response in responses.as_stream():
    channel = response.get("record", {}).get("event", {}).get("channel")
    if not channel:
        continue
    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        json={
            "text": random.choice(["On it", "Runnin' the numbers, gimme a sec", "Lmc, hold tight"]),
            "channel": channel,
        },
        headers={"Authorization": f"Bearer {slack_connection['token']}"},
    )
    resp = handle_rate_limiting(resp)
    if not resp.ok:
        print(resp.json())
        resp.raise_for_status()
