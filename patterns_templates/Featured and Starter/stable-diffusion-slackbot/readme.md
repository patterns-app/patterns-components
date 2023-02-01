# Stable Diffusion Bot

A slack bot that uses Stable Diffusion to create images from text prompts

It takes in a Slack event in via webhook when the bot is mentioned, sends the prompt to
a Stable Diffusion model hosted on [Replicate](https://replicate.com), then responds in
Slack with the generated image.

## Configuration

1. Create a [Slack App](https://api.slack.com/apps).
2. In the Slack app, select `Event Subscriptions` from the left menu.
    * Turn on `Enable Events`
    * Fill in `Request URL` with the URL of the `Slack Mention Webhook` in this graph (select the node and copy the URL)
    * In the `Subscribe to bot events` section, add:
        * `app_mentions`
3. In your new Slack app, select, `OAuth & Permissions` from the left menu.
    * Under `Scopes`, add
      * `chat:write`
    * Under `OAuth Tokens for Your Workspace`, click `Install to Workspace` and authorize the app.
    * Under `OAuth Tokens for Your Workspace`, copy the `Bot User OAuth Token`, which is used to configure the `Respond in Slack` node.
4. Click the `Respond in Slack` node and select the `Settings` tab.
    * For the `slackbot` connection, click `New Connection`
    * Paste the previously copied `Bot User OAuth Token` into the `Bot User OAuth Token` field.
    * Click `Connect`
    * For the `replicate_auth_token` parameter, enter your 
      [Replicate](https://replicate.com) API key.

## Try it out!

In Slack, @mention your bot and say: "@stablediffusionbot a rabbit in a
field", and it should start a thread and respond with the generated image.

## More Information
Check out [intro to streaming and webhooks](https://www.patterns.app/docs/dev/streams) or the
[python reference](https://www.patterns.app/docs/reference/python-reference) in the docs
for more details on working with webhooks and streaming data in Patterns.
