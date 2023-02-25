# Building a GPT-3 chatbot from Algolia

Generate GPT-3 text completions from a prompt of algolia search results. 

## Configuration

### Slack

https://api.slack.com/apps

Follow readme for each Slack node or use the following app manifest and install into your Slack org

Configure the bot with the following webhook:
::Webhook{#vgi2t74o}

#### Sample manifest:
```yml
display_information:
  name: Patterns Helpdesk
  description: A chatbot to help with Patterns related questions
  background_color: "#000000"
features:
  bot_user:
    display_name: Patterns Helpdesk
    always_online: false
oauth_config:
  scopes:
    user:
      - chat:write
    bot:
      - app_mentions:read
      - incoming-webhook
      - chat:write
      - chat:write.public
settings:
  event_subscriptions:
    request_url: <your-slack-webhook-url>
    bot_events:
      - app_mention
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
  ```

### Alogolia

https://www.algolia.com/account/api-keys/all

Configure APIs inside :Node{#emxnhuad}

### OpenAI

https://platform.openai.com/account/api-keys

**Note:** Be sure to check if you have an open ai credits that are not expired https://platform.openai.com/account/usage

The default prompt:

```python
prompt_template = (
    "{answer}\n"
    "{question}?\n"
)
```

Temperature set to 0.75

## Open AI costs

Each text completion, cost around 1k tokens with `davinci-002` or a total $0.02




