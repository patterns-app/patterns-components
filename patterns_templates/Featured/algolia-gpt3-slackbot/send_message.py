from patterns import Parameter, Table, Connection

import requests

completions = Table("completions")
slack = Parameter("slackbot", type=Connection("slackbot"))

for c in completions.as_stream().consume_records():
    requests.post(
        "https://slack.com/api/chat.postMessage",
        json={
            "text": c["completion"],
            "channel": c["slack_channel"],
            "thread_ts": str(c["ts"])
        },
        headers={"Authorization": f"Bearer {slack['token']}"},
    ).raise_for_status()
