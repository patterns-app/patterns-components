from patterns import (
    Parameter,
    State,
    Table,
)
from datetime import datetime, timedelta


discord_messages = Table("discord_messages", "r")
bounces = Table("bounces", "w")
discord_messages_filtered = Table("discord_messages_filtered", "w")


state = State()
buffer_seconds = 15
max_q_len = 500


last_message = state.get_datetime("last_message_at")


for message in discord_messages.as_stream():
    message["question"] = message["record"]["data"]["options"][0]["value"]
    if (last_message and last_message > datetime.now() - timedelta(seconds=buffer_seconds)) or (
        len(message["question"]) > max_q_len
    ):
        bounces.append(message)
    else:
        discord_messages_filtered.append(message)
    last_message = datetime.now()


state.set_value("last_message_at", last_message)
