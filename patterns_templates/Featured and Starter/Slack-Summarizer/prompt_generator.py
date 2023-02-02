import json

from patterns import Table
from .slack import Message

commands_table = Table("commands")
sessions_table = Table("sessions")
prompts_table = Table("prompts", mode="w")


def make_prompt_messages(session) -> list[dict]:
    messages = [Message(**j) for j in json.loads(session["messages"])]
    messages.sort(key=lambda x: x.ts)
    messages_json = []
    for m in messages:
        message_json = {
            "u": m.user,
            "t": m.text,
        }
        if replies := m.replies:
            replies.sort(key=lambda x: x.ts)
            message_json["r"] = [{
                "u": r.user,
                "t": r.text
            } for r in replies]
        messages_json.append(message_json)

    return messages_json


def summarize(session):
    messages = make_prompt_messages(session)

    return f"""
    Here are a list of messages in JSON format.

    {json.dumps(messages)[:3000]}

    Please summarize the messages and respond with bullets in markdown format.
    """


def query(session, command):
    messages = make_prompt_messages(session)

    return f"""
    Here are a list of messages in JSON format.

    {json.dumps(messages)[:3000]}

    Please respond to this question in Markdown format: {command["command"]} 
    """


with commands_table.as_stream().consume_with_rollback() as safe_stream:
    for command in safe_stream:
        session_key = command["session_key"]
        sessions = sessions_table.read_sql(f"select * from {sessions_table} where key = '{session_key}'")

        if not sessions:
            print(f"No session found for session_key={session_key}")
            continue

        session = sessions[0]
        if command["command"] == 'summarize':
            prompt = summarize(session)
        else:
            prompt = query(session, command)

        prompts_table.write({
            "prompt": prompt,
            "channel": session["channel"],
            "thread_ts": session["thread_ts"],
            "user": command["user"],
        })
