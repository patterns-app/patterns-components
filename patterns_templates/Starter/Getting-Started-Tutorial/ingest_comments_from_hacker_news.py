from patterns import (
    Parameter,
    State,
    Table,
)

import requests 

# define table objects
comments = Table('comments', mode='w')

# set urls 
hn_url_stub = "https://hacker-news.firebaseio.com/v0/item/"
hn_url_latest_item = "https://hacker-news.firebaseio.com/v0/maxitem.json"

# get latest item from hacker news
latest_item = requests.get(hn_url_latest_item).json()

# get last 100 comments from hacker news 
count_items = 100
starting_item = latest_item - count_items 

for i in range(starting_item, latest_item):
    url = hn_url_stub + str(i) + '.json'
    record = requests.get(url).json()
    if record["type"] == "comment":
        comments.append(record)
