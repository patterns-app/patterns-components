# Slack Summarizer Bot

A proof-of-concept GPT-3 slack bot that summarizes Slack channels in response to Slack @ mentions.

It takes in a Slack event in via webhook, creates a GPT prompt,
sends it to OpenAI's davinci GPT-3 model, and then responds in Slack with the 
OpenAI completion.

## Configuration

1. Create a [Slack App](https://api.slack.com/apps).
2. In the Slack app, select `Event Subscriptions` from the left menu.
    * Turn on `Enable Events`
    * Fill in `Request URL` with the URL of the `Slack Mention Webhook` in this graph (select the node and copy the URL)
    * In the `Subscribe to bot events` section, add:
        * `app_mentions`
3. In your new Slack app, select, `OAuth & Permissions` from the left menu.
    * Under `Scopes`, add
      * `channels:history`
      * `users:read`
      * `chat:write`
      * `groups:history` (if you also want to summarize private channels) 
    * Under `OAuth Tokens for Your Workspace`, click `Install to Workspace` and authorize the app.
    * Under `OAuth Tokens for Your Workspace`, copy the `Bot User OAuth Token`, which is used to configure the `Respond in Slack` node.
4. Click the `Respond in Slack` node and select the `Settings` tab.
    * For the `slackbot` connection, click `New Connection`
    * Paste the previously copied `Bot User OAuth Token` into the `Bot User OAuth Token` field.
    * Click `Connect`
5. Click the `OpenAI GPT-3 Completion` node and select the `Settings` tab.
    * Select the connection, and either create a new connection or select an existing one.

## Try it out!

**Note** The first time you run this graph, you need to manually run the :Node{#zgysrpm7} node.  This
imports the users from Slack and creates the users table.  After that, the user list will automatically
refresh every day.

In Slack, @mention your bot and say: "@summarizerbot summarize #eng", and it should
start a thread and respond with the summary.

In the thread, you can continue to interact with the bot to get more information about
the summary: "@summarizerbot were there any meetings?"

## More Information
Check out [intro to streaming and webhooks](https://www.patterns.app/docs/dev/streams) or the
[python reference](https://www.patterns.app/docs/reference/python-reference) in the docs
for more details on working with webhooks and streaming data in Patterns.