import requests
from patterns import *

url = "https://api.peopledatalabs.com/v5/person/bulk"

emails = Table("emails")
email_stream = emails.as_stream()

enriched_emails = Table("enriched_emails", mode="w")
errors = Table("errors", "w")

api_key = Parameter("pdl_api_key", type=str, description="People Data Labs api key")

records = list(email_stream.consume_records())
if len(records) > 0:
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    data = {
        "requests": [
            {
                "params": {
                    "email": c["email"],
                    "first_name": c["first_name"],
                    "last_name": c["last_name"],
                }
            }
            for c in records
        ]
    }
    response = requests.post(url, headers=headers, json=data)

    responses = response.json()
    assert len(responses) == len(records)
    for original, response in zip(records, responses):
        status = response["status"]
        if status in (400, 401, 402, 405, 429):
            # Correctable errors (user can fix them)
            email_stream.rollback()
            raise Exception(f"Error enriching: {response}")
        elif status >= 500:
            email_stream.rollback()
            raise Exception("PDL internal error")
        elif status == 200:
            original.update(response["data"])
            enriched_emails.append(original)
        else:
            # If other non-correctable error (404 for instance)
            original["error"] = response["error"]
            errors.append(original)
