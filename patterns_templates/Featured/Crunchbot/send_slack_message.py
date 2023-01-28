from patterns import (
    Parameter,
    State,
    Table,
    Connection,
)
import requests
import json
from patterns_components.helpers.api import handle_rate_limiting
from tabulate import tabulate

responses = Table("results")
slack_connection = Parameter("slackbot_connection", type=Connection("slackbot"))

state = State()
state.set_value("latest_streamed_dshjjq6i_patterns_id", "01gq5tn7d1gkenz9dwqfapdqaa")

def format_result(res):
    if res and isinstance(res, list):
        return tabulate(res, headers="keys")
    return res


for response in responses.as_stream():
    if not response["slack_channel"]:
        continue
    res = json.loads(response['result'])
    print(res)
    msg = f"""Here's the answer I got:

```
{format_result(res['result'])[:2500]}
```

And the SQL I used:

```
{res['sql'].strip()}
```
"""
    json_data = {
            "text": msg,
            "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": msg},
                    }
            ],
            "channel": response["slack_channel"],
        }
    print(json_data)
    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        json=json_data,
        headers={"Authorization": f"Bearer {slack_connection['token']}"},
    )
    resp = handle_rate_limiting(resp)
    if not resp.ok:
        print(resp.json())
        resp.raise_for_status()
    print(resp.json())
