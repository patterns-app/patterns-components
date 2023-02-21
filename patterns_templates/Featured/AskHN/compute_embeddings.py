from patterns import (
    Parameter,
    State,
    Table,
    Connection,
)
import pinecone
import openai
  

import pickle
import time
from itertools import islice

import openai
from openai.error import RateLimitError
from patterns import Parameter, Table, State


state = State()

api_key = Parameter("pinecone_api_key")
openai_conn = Parameter("openai_api_key", type=Connection("openai"))
openai.api_key = openai_conn["api_key"]


docs = Table("docs")


pinecone.init(api_key=api_key, environment="us-east1-gcp")
pc_index_name = "hn-sample"
if pc_index_name not in pinecone.list_indexes():

    try:
        pinecone.create_index(pc_index_name, dimension=1536)
    except Exception as e:
        print(e)

# connect to index
index = pinecone.Index(pc_index_name)


def get_embedding(input_text: str) -> list[float]:
    result = openai.Embedding.create(model="text-embedding-ada-002", input=input_text)
    return result["data"][0]["embedding"]


inputs_stream = docs.as_stream()
inputs_iter = iter(inputs_stream)
retry_count = 0

while state.should_continue():
    records: list[dict] = list(islice(inputs_iter, 10))
    if not records:
        break
    try:
        try:
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=[r["doc"] for r in records],
            )
        except RateLimitError as e:
            inputs_stream.rollback()
            retry_count += 1
            if retry_count > 30:
                raise
            print(f"Hit Rate limit, sleeping for {retry_count}s: {e}")
            time.sleep(retry_count)
            continue
        vectors = [(str(records[data.index]["id"]), data.embedding) for data in response.data]
        index.upsert(vectors)
        inputs_stream.checkpoint()
    except Exception:
        inputs_stream.rollback()
        raise
else:
    state.request_new_run()




