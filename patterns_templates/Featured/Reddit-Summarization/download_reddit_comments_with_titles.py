from patterns import (
    Parameter,
    State,
    Table,
)
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment

subreddit = Parameter(
    "subreddit",
    type=str,
    description="The URL name of the subreddit you wish to summarize"
)

links_to_scrape = Parameter(
    "links_to_scrape",
    type=int,
    description="The number of the top links to scrape."
)

top_external_posts = Table("reddit_comments", "w")

def get_link(url):
    # we scrape the public website since it does not require you to log in with your reddit username and password
    cookies = {
        'loid': '0000000000uym58evp.2.1670967106000.Z0FBQUFBQmptTzlDNGYzb251VFVkWFVrM2ZvUXFiNjhjT2NLU2Vic0szT0hIdExnRldOT0F2dTFZcVdUWXFVVnFkeFp6d3ZaYVpEQTBzN0FpYTVoRTVlRlY3T0lkVG8tNlpaZTlhMDcycjh1RnhuM1pJaWwxN0tvV25wZFN0amdVSW1LWi1VQXJVSG8',
        'token_v2': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NzEwNTMzODYsInN1YiI6Ii0yRUo2QWFqN2k5M1gzYTlLSHJPZ1M5bzJ2YlowdGciLCJsb2dnZWRJbiI6ZmFsc2UsInNjb3BlcyI6WyIqIiwiZW1haWwiLCJwaWkiXX0.x-ZSGip-mWYHcV4ZyzWNtVR4Hbo_X-VqBvVOaJAqU6I',
        'csv': '2',
        'edgebucket': 'AMACHZEmTMXS7u1Q6C',
        'datadome': 'GIX6I93ZlXlohqn7PYf4j_VfHFJ47kjea8K44GjJ0b~XVRkS~NCEijw~fueEzdxFJh7DMPk0lys4P66tTJfxGHGt70LiSjDaFlD7qHT7qNAxPgk60kpEeU4otn0FG05',
        'recent_srs': 't5_2rb5s%2C',
        'USER': 'eyJwcmVmcyI6eyJnbG9iYWxUaGVtZSI6IlJFRERJVCIsImNvbGxhcHNlZFRyYXlTZWN0aW9ucyI6eyJmYXZvcml0ZXMiOmZhbHNlLCJtdWx0aXMiOmZhbHNlLCJtb2RlcmF0aW5nIjpmYWxzZSwic3Vic2NyaXB0aW9ucyI6ZmFsc2UsInByb2ZpbGVzIjpmYWxzZX0sIm5pZ2h0bW9kZSI6ZmFsc2UsInN1YnNjcmlwdGlvbnNQaW5uZWQiOmZhbHNlLCJ0b3BDb250ZW50RGlzbWlzc2FsVGltZSI6MCwidG9wQ29udGVudFRpbWVzRGlzbWlzc2VkIjowfX0=',
        'session': '12fc3f1a3f6536f4c8cece005139a8165f1402f9gAWVSQAAAAAAAABKRu+YY0dB2OY70YpZxX2UjAdfY3NyZnRflIwoOTdiZTIwMzFhYmNiMTA4MzUwNmJjMmU0MTc1Yjk1Y2ZkOWVkOWQ5NpRzh5Qu',
        'session_tracker': 'jmngmdehkenkfehejr.0.1670967110219.Z0FBQUFBQmptTzlHaVNRUEluenp2RlNrbjNOekMzYmxfcnZCMnVkd2Q4LWcxbEdpZEFJcE5LekpwYWNtZ3FmTW9LSDNHUVQxRjREZF9VVXFLRlZ0MnFjaFQtVkN3Um0zT3IwQkJ0SnlobWlqQmhNZUJhMDVHUFpYZjlZRmpQZFlHcDRpZGFJSlByUFc',
    }

    headers = {
        'authority': 'www.reddit.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    }

    res = requests.get(url, cookies=cookies, headers=headers)
    return res.text


def get_comment_links(subreddit, elements):
    # NOTE: The posts are ordered as they would be in the site, so we can take this as the "top [n] posts" from the subreddit
    # NOTE: alb.reddit.com links are ads
    # NOTE: Any links that start with a / are links to the subreddit itself
    return list(filter(
        lambda x: f"old.reddit.com/r/{subreddit}/comments" in x["href"],
        elements))

# 1 token is ~ 4 characters when in english according to: https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
# the maximum number of tokens for a completion is ~4000
chunk_size = 4000 * 3

subreddit_tree = BeautifulSoup(get_link("https://old.reddit.com/r/" + subreddit))
entries = subreddit_tree.select(".entry")
for entry in entries[:links_to_scrape]:
    title = entry.select_one('.title').getText()
    comments_link = entry.select_one('.first a')
    if comments_link is None:
        # print(entry)
        continue
    comments_href = comments_link["href"]
    tree = BeautifulSoup(get_link(comments_href))

    all_comment_text = ""
    comments = tree.select("div.entry form div div p")
    for comment in comments:
        all_comment_text += comment.getText() + "\n"

    chunk_index = 0
    for i in range(0, len(all_comment_text), chunk_size):
        chunk_text = all_comment_text[i:i+chunk_size]

        top_external_posts.append({
            "title": title,
            "href": comments_href,
            "chunk_text": chunk_text,
            "chunk_index": chunk_index
        })

        chunk_index += 1