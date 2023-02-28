# OpenAI Generate Text Embeddings

For each record in the connected input table,

use OpenAI to compute embedding for the record, add it to the record as an `embedding` field,
and then write the updated record to the connected output table.

## Parameters

- `connection` Your authenticated OpenAI connection
- `model` The OpenAI embed model to use. Defaults to `text-embedding-ada-002`
- `max_number` The max number of records to create embeddings for. Defaults to `1000`

## Inputs

- `input_texts` The table to build embeddings for

## Outputs

- `embeddings` The table to write embeddings to
