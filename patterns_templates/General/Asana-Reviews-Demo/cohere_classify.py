import re

import cohere
from cohere.classify import Example
from patterns import Parameter, State, Table, Connection


cohere_connection = Parameter(
    "cohere_connection", type=Connection("cohere"), default=None
)
input_text_column = Parameter("Input Text Column")
example_text_column = Parameter("Example Text Column")
example_category_column = Parameter("Example Category Column")
auto_truncate = Parameter("auto_truncate", type=bool, default=True)

training_data_table = Table("cohere_examples")
test_data_table = Table("cohere_inputs")
cohere_output_table = Table("cohere_output", "w")

co = cohere.Client(cohere_connection.get("api_key"))
input_stream = test_data_table.as_stream()


def cohere_truncate(text):
    # According to cohere documentation: https://docs.cohere.ai/docs/tokens#:~:text=Suggest%20Edits,have%20their%20own%20unique%20tokens.
    # One word can be 1 or more tokens. So assuming each word is 3 tokens,
    # that means we can have a maximum of roughly 512 / 3 words in our text.
    # This is a rough and likely conservative calculation
    return "".join(re.split(r"(\s+)", text, maxsplit=512)[: 2 * 512 // 3 - 1])


example_data = training_data_table.read()

training_examples = []
for example in example_data:
    text = example[example_text_column]
    category = example[example_category_column]
    if auto_truncate:
        text = cohere_truncate(text)
    training_examples.append(Example(text, category))


def predict_batch(records: list[dict]) -> list[dict]:
    response = co.classify(
        model="large",
        inputs=[cohere_truncate(r[input_text_column]) for r in records],
        examples=training_examples,
    )
    for record, resp in zip(batch, response):
        record["prediction"] = resp.prediction
        record["confidence"] = resp.confidence
    return batch


batch = []
batch_size = 64
try:
    for record in input_stream:
        batch.append(record)
        if len(batch) >= batch_size:
            print(f"Classifying batch of {batch_size} inputs")
            cohere_output_table.append(predict_batch(batch))
            input_stream.checkpoint()
            batch = []
    if batch:
        cohere_output_table.append(predict_batch(batch))
except Exception as e:
    # Rollback to last checkpoint() if an error so we retry the records next time
    input_stream.rollback()
    raise e
