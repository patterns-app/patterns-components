# Cohere co.classify

Classifies the input texts based on your input examples using the [cohere classify](https://docs.cohere.ai/reference/classify) API!

## Parameters
 - `cohere_connection` Your authenticated cohere connection
 - `Input Text Column` The column of the `cohere_inputs` table that your cohere input text will come from
 - `Example Text Column` The column of `cohere_examples` that the cohere example text will come from
 - `Example Category Column` The column of `cohere_examples` that the cohere "tag" will come from.
 - `Auto Truncate` Whether or not you want this component to automatically truncate texts that are too long. Tokens are approximate with cohere's model so the exact number of tokens cannot be determined, however this component will do a "best effort" to truncate texts that it thinks will exceed 512 tokens in cohere's API.

## Inputs
 - `cohere_inputs` The inputs you wish to run the cohere classifier on
 - `cohere_examples` The cohere examples you wish to use to teach cohere's language model

## Outputs
 - `cohere_output` Cohere's predictions and their respective confidences
