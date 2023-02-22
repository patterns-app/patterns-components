from patterns import (
    Parameter,
    State,
    Table,
    Connection,
)
import pinecone
import openai


discord_messages_filtered = Table("discord_messages_filtered", "r")


api_key = Parameter("pinecone_api_key")
openai_conn = Parameter("openai_api_key", type=Connection("openai"))
openai.api_key = openai_conn["api_key"]


docs = Table("docs")
discord_hits = Table("discord_hits", "w")

pinecone.init(api_key=api_key, environment="us-east1-gcp")
pc_index_name = "hn-sample"
index = pinecone.Index(pc_index_name)


def query(text):
    response = openai.Embedding.create(
    input=text,
    model="text-embedding-ada-002"
    )
    embed = response['data'][0]['embedding']
    resp = index.query(
        vector=embed,
        top_k=3,
        include_values=False
    )
    return resp, embed


for msg in discord_messages_filtered.as_stream():
    question = msg["question"]
    resp, embed = query(question)
    msg["matches"] = [{"id": m["id"], "score": m["score"]} for m in resp["matches"]]
    msg["question_embedding"] = {"embedding": embed}
    discord_hits.append(msg)








