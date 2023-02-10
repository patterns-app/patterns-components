from patterns import (
    Parameter,
    State,
    Table,
)
import re

mentions = Table("mentions", "r")
questions = Table("questions", "w")


for mention in mentions.as_stream():
    event = mention["record"].get("event")
    if not event:
        continue
    question = event["text"]
    question = re.sub(r"<@.*>", "", question)
    channel = event["channel"]
    questions.append({"question": question, "slack_channel": channel, "email_sender": None, "message_id": None})