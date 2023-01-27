from patterns import (
    Parameter,
    State,
    Table,
)


messages = Table("messages", "r")
questions = Table("questions", "w")


for m in messages.as_stream():
    questions.append({"question": m["subject"], "slack_channel": None, "email_sender": m["from"], "message_id": m["message_id"]})