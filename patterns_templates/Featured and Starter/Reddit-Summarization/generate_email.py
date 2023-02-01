from patterns import (
    Parameter,
    State,
    Table,
)
import requests
import json

completions_table = Table("completions", "r")
completion_chunks = completions_table.read()
emails = Table("emails", "w")

recipient_email = Parameter(
    "recipient_email",
    type=str,
    description="The email you wish to send the newsletter to"
)

subreddit = None
message = ""

completions = {}
for chunk in completion_chunks:
    href = chunk["href"]
    if href not in completions:
        completions[href] = []

    completions[href].append(chunk)

for href, chunks in completions.items():
    all_completions = "\n<br />\n".join([
        i["completion"] for i in 
        sorted(
            chunks,
            key=lambda x: x["chunk_index"]
        )
    ])
    title = chunks[0]['title']
    subreddit = href.split("/")[4]
    message += f"""
<b> {title} </b> [<a href="{href}">source</a>]

<blockquote>
    {all_completions}
</blockquote>

"""

emails.append({
    "recipient": recipient_email,
    "subject": f"What does reddit think about r/{subreddit}",
    "body": message.encode("ascii", "ignore").decode("ascii")
})