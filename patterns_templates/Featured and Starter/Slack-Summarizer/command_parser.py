import re
import time

from patterns import Connection, Parameter, State, Table
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from .slack import SlackClient

auth = Parameter("slack", type=Connection("slackbot"))
hours_back = Parameter("hours_back", type=int, default=72)
slack = WebClient(token=auth["token"])
users_table = Table("users", "r")
commands_table = Table("commands", "w")
slack_events = Table("slack_events", "r")
session_table = Table("sessions", "w")
session_table.init(unique_on="key")

users_by_id = {}
for user in users_table.read_sql(f"select * from {users_table}"):
    users_by_id[user.get("id")] = user

s = State()
if not s.get_value("initialized", False):
    session_table.write({
        "key": "bogus",
        "channel": "",
        "thread_ts": "",
        "initiating_user": "",
        "messages": [],
    })
    session_table.flush()
    s.set_value("initialized", True)


def session_key(channel: str, thread_ts: str) -> str:
    return f"{channel}_{thread_ts}"


for m in slack_events.as_stream():
    event = m["record"].get("event")
    if not event or not event.get("type") == 'app_mention':
        continue

    channel = event["channel"]
    if thread_ts := event.get("thread_ts"):
        # We are mentioned in a thread.
        ...
    else:
        thread_ts = event.get("ts")

    key = session_key(channel, thread_ts)

    sessions = session_table.read_sql(f"SELECT * FROM {session_table} WHERE key = '{key}'")
    if len(sessions) == 0:
        vals = re.findall(r"<@(U[A-Z0-9]+)> summarize <#(C[A-Z0-9]+)[^>]+>", event["text"])
        if not vals:
            slack.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=f"Sorry, <@{event['user']}>.  The syntax is:  @bot summarize #channel"
            )
            continue

        summarize_channel = vals[0][1]

        # Quickly respond to the user
        slack.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=(f"<@{event['user']}> 👍   I'm off to summarize <#{summarize_channel}>. "
                  " I'll post the results here when I'm done.")
        )

        client = SlackClient(
            channel_id=summarize_channel,
            oldest_message_time=time.time() - 60 * 60 * hours_back,
            users_by_id=users_by_id,
            client=slack
        )

        try:
            messages = client.get_channel_messages()
        except SlackApiError as e:
            slack.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=f"Sorry, <@{event['user']}>.  An error occurred:  {e.response['error']}"
            )
            continue


        session_table.write({
            "key": key,
            "channel": channel,
            "thread_ts": thread_ts,
            "initiating_user": event["user"],
            "messages": [m.dict() for m in messages],
        })
        session_table.flush()

        commands_table.write({
            "session_key": key,
            "command": "summarize",
            "user": event["user"],
            "channel": channel,
        })
    elif len(sessions) == 1:
        vals = re.findall(r"<@(U[A-Z0-9]+)>(.*)", event["text"])

        commands_table.write({
            "session_key": key,
            "command": vals[0][1].strip(),
            "user": event["user"],
            "channel": channel,
        })
    else:
        raise ValueError(f"Multiple sessions with the same key: {key}")

