# Configure to receive Slack messages

To configure this webhook to receive @ mentions from slack, copy the webhook URL above and follow
these steps:

1. Create a [Slack App](https://api.slack.com/apps).
2. In the Slack app, select `Event Subscriptions` from the left menu.
    * Turn on `Enable Events`
    * Fill in `Request URL` with the URL of the webhook above
    * In the `Subscribe to bot events` section, add:
        * `app_mention`

## Try it out!

In Slack, @mention your bot and you will see the message appear in the attached `slack_messages`
table.
