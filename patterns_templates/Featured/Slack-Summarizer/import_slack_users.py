from patterns import Connection, Parameter, State, Table
from slack_sdk import WebClient

auth = Parameter("slack", type=Connection("slackbot"))
slack = WebClient(token=auth["token"])

user_table = Table("users", mode="w")
user_table.init(unique_on="id")

next_cursor = None
while True:
    users_list = slack.users_list(limit=1000, cursor=next_cursor)
    users_list.validate()
    user_table.upsert(users_list.get("members", []))
    next_cursor = users_list.get("response_metadata", {}).get("next_cursor", '')
    if not next_cursor:
        break
