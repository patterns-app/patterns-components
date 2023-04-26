from patterns import Parameter, Table

import requests

replicate_token = Parameter("replicate_auth_token", description="Paste in your Replicate token: https://replicate.com/account")

prompt = Parameter('1. prompt', default='an astronaut riding a horse on mars, hd, dramatic lighting', description="Input prompt")
negative_prompt = Parameter('2. negative_prompt', default='', description="Specify things to not see in the output")
num_inference_steps = Parameter('3. num_inference_steps', default=50, type=int, description='Number of denoising steps (minimum: 1; maximum: 500)')
guidance_scale = Parameter('4. guidance_scale', default=7.5, type=float, description='Scale for classifier-free guidance (minimum: 1; maximum: 20)')
scheduler = Parameter('5. scheduler', default='K_EULER', description='Choose a scheduler')
seed = Parameter('6. seed', type=int, default=None, description='Random seed. Leave blank to randomize the seed')
model_version = Parameter('model_version', default='db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf', description="Versions: https://replicate.com/stability-ai/stable-diffusion/versions")

# Set the API endpoint URL
url = "https://api.replicate.com/v1/predictions"

# Set the request headers
headers = {
    "Authorization": f"Token {replicate_token}",
    "Content-Type": "application/json"
}

payload_input = {
    "prompt": prompt,
    "negative_prompt": negative_prompt,
    "num_inference_steps": num_inference_steps,
    "guidance_scale": guidance_scale,
    "scheduler": scheduler,
}

# If seed is not set, then it will be random
if seed is not None:
    payload_input['seed']: seed

# Set the request payload
payload = {
    "version": model_version,
    "input": payload_input
}


# Send a POST request to the API
response = requests.post(url, json=payload, headers=headers)

# Access the response data
response_data = response.json()

results = Table("results", "w")

results.append(response_data)