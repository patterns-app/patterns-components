# Sales Lead Email Generator

Use GPT3 to generate an email that a business might send to a prospective customer

This example application generates an email that a business might send to a
prospective customer.  The customer fills in a form, and a sample email message
for contacting them is sent to a Slack channel.  Salespeople can watch their
incoming Slack messages and use the email as a starting point for reaching
out to the customer.  This app uses GPT from OpenAI to generate emails based
on the customer form submission.

The steps of the app are:
1. Receive form submission from Typeform
2. Turn the form into a GPT prompt
3. Use OpenAI's GPT to turn the prompt into a sales email
4. Post the example email to Slack, giving the salesperson a contact and sample to work from.
  
  


## Setup
To use this app, you'll need to configure a couple things:

1. Tell Typeform to send your form submissions to the webhook.  This is done from their `Connection -> Webhooks` menu.  The Webhook URL is available in the `Details` tab, after clicking on the Typeform Webhook node.
2. Create an OpenAI connection.  You can do this by clicking the OpenAI node and configuring
the Connection parameter.
3. Configure OpenAI GPT3 completion component, changing the prompt and form elements in the code.
4. Configure the `Post Email Example to Slack` component, giving it the Webhook URL to post to.  This can be found in the`Incoming Webhook` section of [the Slack API site.](https://api.slack.com/apps)