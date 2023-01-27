# Send Slack Message

Starter node for sending each record in a table as a Slack message. Connected
`messages` table, the fields of which can be used in the message template.

### Inputs
- `messages` - Messages table, each record of which will be sent as a Slack message

### Parameters

- `slack_webhook_url` - A slack "Incoming Webhook", see here for instructions: https://api.slack.com/messaging/webhooks
- `message_template` - Template for slack message, for example `'Hello {name}, it is {time}'`, where 
   `name` and `time` are fields in the record. Slack supports a simplified **markdown** syntax.
   
