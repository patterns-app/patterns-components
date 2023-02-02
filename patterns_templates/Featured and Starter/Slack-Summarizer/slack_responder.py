from patterns import Table, Parameter, Connection
from slack_sdk import WebClient

completions = Table("completions", "r")
auth = Parameter("slack", type=Connection("slackbot"))
slack = WebClient(token=auth["token"])

with completions.as_stream().consume_with_rollback() as records:
    for record in records:
        slack.chat_postMessage(
            channel=record["channel"],
            thread_ts=str(record["thread_ts"]),
            text=record["completion"],
        ).validate()
