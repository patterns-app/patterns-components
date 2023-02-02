# Send Gmail email

Starter node for sending each record in a table as an email via an authed Gmail account. Connected
`emails` table should have three columns for `recipient`, `subject`, and `body`.

### Inputs
- `emails` - Emails table, each record of which will be sent as an email

### Parameters

- `sender_email` - Gmail email of the sender
- `gmail_app_password` - A Gmail app password created for the sender email. Create one here: 
   security.google.com/settings/security/apppasswords
- `delay_seconds` - Seconds to delay between email sends. Defaults to 1
