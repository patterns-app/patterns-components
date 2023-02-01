from patterns import (
    Parameter,
    State,
    Table,
)

import imaplib
import email
import email.policy

messages = Table("messages", "w")

pw = Parameter("gmail_app_password")
mail=imaplib.IMAP4_SSL("imap.gmail.com")
mail.login("kvh@patterns.app", pw)
mail.select('automations')


if messages.exists:
    all_messages = {m["message_id"] for m in messages.read()}
else:
    all_messages = set()


def get_msg_object(data):
    for response_part in data:
        if isinstance(response_part, tuple):
            return email.message_from_string(response_part[1].decode("utf-8"), policy=email.policy.default)


def get_recent_messages(n):
    resp_code, response = mail.search(None, "ALL")
    ids = response[0].decode('utf-8').split()[:n]
    for uid in ids:
        status, data = mail.uid('fetch', uid, '(RFC822)')
        msg = get_msg_object(data)
        yield msg


for msg in get_recent_messages(100):
    msg_id = msg.get("Message-ID")
    if msg_id in all_messages:
        continue
    messages.append({
        "from": msg.get("From"),
        "to": msg.get("To"),
        "subject": msg.get("Subject"),
        "message_id": msg_id,
    })





