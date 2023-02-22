from patterns import (
    Parameter,
    State,
    Table,
    Connection,
)
import openai
from scipy import spatial
import tiktoken
import pinecone
from .base import add_text_till_limit
import html


discord_hits = Table("discord_hits", "r")
hn_data = Table("top_comments")
responses = Table("responses", "w")


openai_conn = Parameter("openai_api_key", type=Connection("openai"))
openai.api_key = openai_conn["api_key"]

#completion_model = "chat-davinci-003-alpha"
completion_model = "text-davinci-003"

state = State()
max_comment_chars = 10000


def get_comments(ids, n=20, depth=2):
    comments = []
    for i in range(depth):
        id_clause = ",".join(str(i) for i in ids)
        new_comments = hn_data.read_sql(f"select * from {hn_data} where parent in ({id_clause})")
        if not new_comments:
            break
        comments.extend(new_comments)
        ids = [c["id"] for c in new_comments]
    print(len(comments), f"comments found at depth {depth}")
    comments = sorted(comments, key=lambda c: c["score"], reverse=True)
    return comments[:n]


def get_embeddings(docs):
    n = 10
    vectors = []
    for i in range(len(docs) // n + 1):
        batch = docs[i*n:(i+1)*n]
        if not batch:
            break
        response = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=batch,
        )
        vectors.extend([data.embedding for data in response.data])
    return vectors


def sort_similar_comments(comments, question_vector):
    vectors = get_embeddings([c["post_text"][:max_comment_chars] for c in comments])
    sims = [(1 - spatial.distance.cosine(question_vector, v), i) for i, v in enumerate(vectors)]
    sims = sorted(sims, reverse=True)
    return [comments[i] for v, i in sims]


def summarize_matches_with_comments(msg, max_tokens=3400):
    comments = []
    for m in msg["matches"]:
        comments.extend(get_comments([m["id"]]))
    sorted_cmnts = sort_similar_comments(comments, msg["question_embedding"]["embedding"])
    text, tokens = add_text_till_limit((c["post_text"][:max_comment_chars] for c in sorted_cmnts), max_tokens, "\n\n")
    return text
 

def answer_question(msg):
    text = summarize_matches_with_comments(msg)
    text = html.unescape(text)
    question = msg["question"]
    prompt = f"""{text}

Answer the following question by summarizing the above comments (where relevant), be specific and opinionated when warranted by the content:

Question: "{question}"

Answer: """

    print(prompt)
    
    resp = openai.Completion.create(prompt=prompt, engine=completion_model, max_tokens=500, temperature=.8)
    print(resp)
    return resp


def format_response(completion, msg):
    links = ", ".join(f"https://news.ycombinator.com/item?id={m['id']}" for m in msg["matches"])
    r =  f"""Question: {msg["question"]}

Answer: {completion}

(See: {links}) 
"""
    return r


for msg in discord_hits.as_stream():
    resp = answer_question(msg)
    msg["response"] = format_response(resp["choices"][0]["text"], msg)
    responses.append(msg)

