from patterns import Connection, Parameter, Table

import requests

replicate_token = Parameter("replicate_auth_token", description="Paste in your Replicate token: https://replicate.com/account")

prompt = Parameter('prompt', default='moon frog')
model_version = Parameter('model_version', default='6359a0cab3ca6e4d3320c33d79096161208e9024d174b2311e5a21b6c7e1131c')

# Set the API endpoint URL
url = "https://api.replicate.com/v1/predictions"

# Set the request headers
headers = {
    "Authorization": f"Token {replicate_token}",
    "Content-Type": "application/json"
}

# Set the request payload
payload = {
    "version": model_version,
    "input": {"prompt": prompt}
}

# Send a POST request to the API
response = requests.post(url, json=payload, headers=headers)

# Access the response data
response_data = response.json()

print(response_data)

results = Table("results", "w")


results.append(response_data)