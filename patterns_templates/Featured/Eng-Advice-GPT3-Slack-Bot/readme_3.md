# OpenAI GPT Completions

For each record in the connected input table, builds a prompt from the `prompt_template`, sends
it to OpenAI for completion, updates the record with the best completion response and 
writes it back to the connected output table.

## Parameters
 - `connection` Your authenticated OpenAI connection
 - `prompt_template` Template for prompt, e.g. 'Question: {question}. Answer: ' where `question` 
    is a field in the input record.
 - `model` The OpenAI model to use. Defaults to `text-davinci-003`
 - `max_tokens` Defaults to 200
 - `temperature` Defaults to .75

## Inputs
 - `prompts` The table to build prompts from

## Outputs
- `completions` The table to write completions to
