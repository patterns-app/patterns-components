import requests
from patterns import Parameter, Table
from patterns_components.helpers.api import handle_rate_limiting


messages = Table("messages")
slack_webhook_url = Parameter("slack_webhook_url", type=str)
message_template = Parameter(
    "message_template",
    description=(
        "Template for slack message, e.g. 'Hello {name}, it is {time}', "
        "where `name` and `time` are fields in the record. Slack supports a simplified **markdown** syntax."
    ),
)


message_stream = messages.as_stream()

# Consume records as a stream, rolling back to previous record if there is an exception
with message_stream.consume_with_rollback() as records:
    for record in message_stream:
        message = message_template.format(**record)
        if not message:
            print("Empty message, skipping")
            continue
        resp = requests.post(
            slack_webhook_url,
            json={
                "text": message,
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": message},
                    }
                ],
            },
        )

        # Handles standard rate limiting headers and errors
        resp = handle_rate_limiting(resp)

        if not resp.ok:
            print(resp.json())
            resp.raise_for_status()
