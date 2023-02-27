from patterns import (
    Parameter,
    State,
    Table,
)

import openai

open_ai_api_key = Parameter('open_ai_api_key')
openai.api_key = open_ai_api_key

search_results = Table("search_results")
completions = Table("completions", "w")

answers = []

for match in search_results.as_stream().consume_records():
    answers.append(match["content"])

question = match['thread']
slack_channel = match['slack_channel']
ts = match['ts']

# Feel free to tweak this how every you'd like:
prompt_template = (
    "{answer}\n"
    "{question}?\n"
)

prompt = prompt_template.format(question=question, answer="\n".join(answers))

completion = openai.Completion.create(
    model="text-davinci-003",
    prompt=prompt,
    max_tokens=200,
    temperature=0.75
)

completion['question'] = question
completion['slack_channel'] = slack_channel
completion['ts'] = ts
completion['completion'] = completion.choices[0].text

completions.append(completion)
