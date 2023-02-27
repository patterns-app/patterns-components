from patterns import (
    Parameter,
    State,
    Table,
    Connection,
)
import re
import requests

slack = Parameter("slackbot", type=Connection("slackbot"))

def clean_text(t: str) -> str:
    # Split on user token (looks like <userid>)
    s = re.split(r"<.+>", t)
    # Split and take longest substring
    return max(s, key=lambda x: len(x))

# If mention is part of a thread, bot should be able to reference the context
def get_thread_replies(channel: str, thread: str) -> str:
    params = dict(channel=channel, ts=thread)
    response = requests.get(
        "https://slack.com/api/conversations.replies",
        params=params,
        headers={"Authorization": f"Bearer {slack['token']}"},
    )
    
    response.raise_for_status()
    result = response.json()
    thread_messages = result['messages']

    thread_messages = list(map(lambda m: clean_text(m['text']), result['messages']))

    full_thread = '\n'.join(thread_messages)

    return [thread_messages[0], full_thread]

slack_messages = Table("slack_messages", "r")

questions = Table("questions", "w")

for mention in slack_messages.as_stream().consume_records():
    event = mention["record"].get("event", {})
    question = clean_text(event["text"])
    thread = question

    # Looks for app mention
    if not event.get("type") == "app_mention":
        print("skipping event, not a mention")
        continue

    # Message is part of a thread
    if event.get('thread_ts') != None:
        question, thread = get_thread_replies(event["channel"], event['thread_ts'])


    questions.append({
        "question": question, 
        "thread": thread, 
        "slack_channel": event["channel"],
        "ts": event["ts"]
    })