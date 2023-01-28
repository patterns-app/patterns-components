import re

import replicate
from slack_sdk import WebClient
from slack_sdk.models.blocks import HeaderBlock, ImageBlock

from patterns import Connection, Parameter, Table

auth = Parameter("slack", type=Connection("slackbot"))
replicate_token = Parameter("replicate_auth_token")
slack_events = Table("slack_events", "r")

slack = WebClient(token=auth["token"])

replicate.default_client.api_token = replicate_token

for m in slack_events.as_stream():
    event = m["record"].get("event")
    if not event or not event.get("type") == "app_mention":
        continue

    channel = event["channel"]
    thread_ts = event.get("thread_ts") or event["ts"]

    match = re.match(r"<@U[A-Z0-9]+>\s*(.+)", event["text"])
    if not match:
        slack.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=f"Hi, <@{event['user']}! Add some text when you mention me, and I'll generate an image. Try '@bot a rabbit standing in a meadow'",
        )
        continue

    response = slack.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text=f"Hi, <@{event['user']}>! I'm generating an image now. Hold Tight.",
    )
    message_ts = response["ts"]

    prompt = match.group(1).strip()
    try:
        model = replicate.models.get("stability-ai/stable-diffusion")
        image_url = model.predict(prompt=prompt)[0]
    except Exception:
        slack.chat_update(
            channel=channel, ts=message_ts, text="Sorry, something went wrong!"
        )
        raise
    else:
        blocks = [
            HeaderBlock(text=prompt),
            ImageBlock(image_url=image_url, alt_text=prompt),
        ]
        slack.chat_update(channel=channel, ts=message_ts, blocks=blocks, text=prompt)
