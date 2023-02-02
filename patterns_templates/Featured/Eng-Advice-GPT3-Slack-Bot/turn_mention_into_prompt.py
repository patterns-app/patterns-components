from patterns import Parameter, State, Stream, Table
import re


mentions = Table("mentions")
prompts = Table("prompts", "w")
prompts.init(add_created="timestamp")


def clean_text(t: str) -> str:
    # Split on user token (looks like <userid>)
    s = re.split(r"<.+>", t)
    # Split and take longest substring
    return max(s, key=lambda x: len(x))


for mention in mentions.as_stream().consume_records():
    event = mention["record"].get("event", {})

    # Looks for app mention
    if not event.get("type") == "app_mention":
        print("skipping event, not a mention")
        continue

    prompts.append({
        "prompt": clean_text(event["text"]), 
        "slack_channel": event["channel"]
    })
