import requests
from patterns import Parameter, State, Table, Connection
from patterns_components.helpers.api import handle_rate_limiting


_prompt_template_description = (
    "Template for prompt, e.g. 'Question: {message}. Answer: ' "
    "where `message` is a field in the input record."
)

prompts = Table("prompts")
completions = Table("completions", "w")

connection = Parameter("connection", type=Connection("openai"))

prompt_template = "{prompt}"

model = Parameter("model", type=str, default="text-davinci-003")
max_tokens = Parameter("max_tokens", type=int, default=500)
temperature = Parameter("temperature", type=float, default=0.75)
num_completions = 3

api_key = connection.get("api_key")

# Consume the records as a stream, rolling back to previous record if there is an exception
with prompts.as_stream().consume_with_rollback() as records:
    for record in records:

        prompt = prompt_template.format(**record)

        # create a completion
        resp = requests.post(
            "https://api.openai.com/v1/completions",
            json={
                "prompt": prompt,
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "n": num_completions,
            },
            headers={"Authorization": f"Bearer {api_key}"}
        )
        resp = handle_rate_limiting(resp)
        if not resp.ok:
            print(resp.json())
            resp.raise_for_status()

        record[f"completion"] = resp.json()["choices"]
        
        completions.append(record)
