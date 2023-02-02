import smtplib
import time
from email.mime.text import MIMEText

from patterns import Parameter, Table


emails = Table("emails")

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
html_body = Parameter(
    "html_body",
    type=bool,
    description="Whether or not the body of the email should be sent as HTML",
    default=False
)


def send_email(
    sender: str, pwd: str, recipient: str | list[str], subject: str, body: str
):
    recipients = recipient if isinstance(recipient, list) else [recipient]

    msg = MIMEText(body, "html") if html_body else MIMEText(body)

    # me == the sender's email address
    # you == the recipient's email address
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(sender, pwd)
    server.sendmail(sender, recipients, msg.as_string())
    server.close()


with emails.as_stream().consume_with_rollback() as records:
    for message in records:
        send_email(
            sender, pw, message["recipient"], message["subject"], message["body"]
        )
        if delay:
            time.sleep(delay)
