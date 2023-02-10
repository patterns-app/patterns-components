from patterns import (
    Parameter,
    State,
    Table,
    Connection
)
import requests
from email.mime.text import MIMEText
import base64
import requests

connection = Parameter(
    "connection",
    type=Connection("gmail"),
    description="Gmail",
)

sender_email = Parameter(
    "Sender Email",
    type=str,
    description="The email of the sender"
)

drafts_table = Table("drafts")
drafts = drafts_table.read()

def create_draft(to_email, from_email, subject, body):
    message = MIMEText(body)
    message["to"] = to_email
    message["from"] = from_email
    message["subject"] = subject


    raw = base64.urlsafe_b64encode( message.as_string().encode("utf-8") ).decode("utf-8")

    res = requests.post(
        "https://www.googleapis.com/gmail/v1/users/me/drafts",
        json={
            "message": {
                "raw": raw
            }
        },
        headers={
            "content-type": "application/json",
            "Authorization": "Bearer " + connection.get("access_token")
        }
    )

# custom code for OpenAI
def parse_completion(draft):
    """Parses the OpenAI draft into a subject and body"""
    draft = draft.strip()
    subject_start = draft.lower().find("subject")
    subject_end = draft.find("\n")
    return (draft[subject_start:subject_end].strip(), draft[subject_end:].strip())

for record in drafts:
    subject, body = parse_completion(record["completion"])
    create_draft(record["work_email"], sender_email, subject, body)

