import smtplib
import time
from email.mime.text import MIMEText

from patterns import Parameter, Table

responses = Table("results")


sender = Parameter(
    "sender_email",
    description="Email of the sender for which the app password is created.",
)
pw = Parameter(
    "gmail_app_password",
    description="A Gmail app password. Create one here: security.google.com/settings/security/apppasswords",
)
delay = Parameter(
    "delay_seconds",
    type=int,
    description="Seconds to delay between email sends",
    default=1,
)


def send_email(
    sender: str, pwd: str, recipient: str | list[str], subject: str, body: str, message_id: str = None
):
    recipients = recipient if isinstance(recipient, list) else [recipient]

    msg = MIMEText(body)

    # me == the sender's email address
    # you == the recipient's email address
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    if message_id:
        msg['In-Reply-To'] = message_id
        msg['References'] = message_id

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(sender, pwd)
    server.sendmail(sender, recipients, msg.as_string())
    server.close()


for response in responses.as_stream():
    if not response["email_sender"]:
        continue
    name, email = response["email_sender"].split("<")
    first_name = name.split()[0]
    msg = f"""You asked '{response['question']}', here's the result I got:
    
    {response['result']}

And here's the SQL I used:
    
{response['result_sql']}
"""
    send_email(
        sender, pw, email.strip(">"), f"Thanks for your question {first_name}", msg, response["message_id"]
    )
    if delay:
        time.sleep(delay)


