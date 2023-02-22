from patterns import (
    Parameter,
    State,
    Table,
)
import tiktoken

from .base import add_text_till_limit


top_stories = Table("sample", "r")
hn_data = Table("top_comments")
docs = Table("docs", "w")

max_tokens_per_doc = 2000

def get_children(id):
    top_level_comments = hn_data.read_sql(f"select * from {hn_data} where parent = {id} order by score desc limit 10")
    return top_level_comments


for story in top_stories.as_stream(order_by="id"):
    print(story["id"])
    cmnts = get_children(story["id"])
    cmnts_summary, tokens = add_text_till_limit([c["post_text"][:2000] for c in cmnts], max_tokens_per_doc, "\n")
    
    text = f"""Title: {story["title"]}

Comments: {cmnts_summary}   
"""
    docs.append({"id": story["id"], "doc": text})



