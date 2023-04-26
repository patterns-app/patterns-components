from patterns import Parameter, Table

import requests
import time

replicate_token = Parameter("replicate_auth_token")

jobs = Table("jobs")
results = Table("results", "w")

for job in jobs.as_stream():
    # Set the request headers
    headers = {
        "Authorization": f"Token {replicate_token}",
        "Content-Type": "application/json"
    }

    url = job['urls']['get']

    # Send a POST request to the API
    response = requests.get(url, headers=headers)

    # Access the response data
    response_data = response.json()

    max_retries = 10
    retries = 0

    # Check if results are ready
    while response_data.get("status") != "succeeded" and retries < max_retries:
        print("Results not ready, waiting for 5 seconds...")
        time.sleep(5)  # Delay for 5 seconds
        response = requests.get(url, headers=headers)  # Send a GET request to the API
        response_data = response.json()
        retries += 1

    result = response_data['output'][0]

    response_data['result'] = result

    results.append(response_data)
