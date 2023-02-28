import openai
from patterns import Parameter, Table, Connection

input_texts = Table("input_texts")
embeddings = Table("embeddings", "w")

connection = Parameter("connection", type=Connection("openai"))

model = Parameter("model", type=str, default="text-embedding-ada-002")
max_number = Parameter("max_number", type=int, default=1000)
record_field_to_embed = Parameter("record_field_to_embed", type=str)

openai.api_key = connection.get("api_key")

new_records = []
for count, record in enumerate(input_texts.read()):
    if count >= max_number:
        break
    result = openai.Embedding.create(input=record[record_field_to_embed], engine=model)
    # extract the embedding from the result and update the record
    record["embedding"] = result["data"][0]["embedding"]
    new_records.append(record)

embeddings.replace(new_records)
