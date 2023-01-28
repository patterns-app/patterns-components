from patterns import (
    Parameter,
    State,
    Table,
)

question = Parameter("Question")

questions = Table("questions", "w")


if question:
    questions.append({"question": question, "slack_channel": None, "email_sender": None, "message_id": None})