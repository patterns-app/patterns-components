import openai
from numpy import dot
from numpy.linalg import norm
from patterns import Parameter, State, Table, Connection
import json

discord_embeddings = Table("discord_embeddings", "r")
docs_embeddings = Table("docs_embeddings", "r")
issues_embeddings = Table("issues_embeddings", "r")

search_text_table = Table("search_text", "r")
search_text_stream = search_text_table.as_stream()
most_relevant_records = Table("most_relevant_records", "w")
all_relevant_records = Table("all_relevant_records", "w")

most_relevant_records.init(schema_hints={'id': 'Text', 'application_id': 'Text'})

n = Parameter("n", type=int, default=5)
model = Parameter("model", type=str, default="text-embedding-ada-002")

connection = Parameter("connection", type=Connection("openai"))
openai.api_key = connection.get("api_key")

record_sets = {
    'discord': discord_embeddings, 
    'docs': docs_embeddings,
    'issues': issues_embeddings,
    }

def cosine_similarity(a, b):
    return dot(a, b)/(norm(a)*norm(b))

for search_text_record in search_text_stream.consume_records():
    search_text = search_text_record['search_text']
    search_embedding = openai.Embedding.create(input=search_text, engine=model)['data'][0]['embedding']

    updated_records = []
    for record_type, record_set in record_sets.items():
        records = record_set.read()
        for record in records:
            record['similarity'] = cosine_similarity(record['embedding'], search_embedding)
            record['application_id'] = search_text_record['application_id']
            record['interaction_token'] = search_text_record['interaction_token']
            record['search_text'] = search_text
            record['type'] = record_type
            updated_records.append(record)

    similarities = sorted(updated_records, key=lambda x: x['similarity'], reverse=True)
    most_relevant_records.replace(similarities[:n])
    all_relevant_records.replace(similarities)
