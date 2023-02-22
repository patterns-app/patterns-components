from patterns import (
    node,
    Parameter,
    State,
    Table
)

import json
import requests
import time
from datetime import datetime

# NOTE: As per the API documentation, there is no rate limit.
# We can make as many requests as we like, we are just limited by response time.
API_BASE_URL = "https://hacker-news.firebaseio.com/v0"
HOURS = 12
hn_data_import = Table("hn_data_import", "w")
state = State()


def ts2str(ts):
    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


def get_max_id():
    """Finds the largest HackerNews post ID. This allows us to process posts chronologically (ish)."""
    resp = requests.get(f"{API_BASE_URL}/maxitem.json")
    resp.raise_for_status()
    return resp.json()


def pull_item(item_id):
    resp = requests.get(f"{API_BASE_URL}/item/{item_id}.json")
    resp.raise_for_status()
    resp_doc = resp.json()
    if resp_doc == None:
        print(resp.text)
    return resp_doc


def add_missing_fields(item):
    default = {
        "dead": False,
        "kids": [],
        "text": None,
        "title": None,
        "descendants": -1, 
        "url": None,
        "deleted": False,
        "score": 1
    }

    for key, default_value in default.items():
        if key not in item:
            item[key] = default_value
    return item


max_id = get_max_id()
current_id = state.get_value("last_id", max_id)

# this is a clean run, so reset all state and the output table
if current_id == max_id:
    state.reset()
    hn_data_import.reset()

current_ts = state.get_value("current_ts", time.time())
one_period_ago_ts = state.get_value("one_period_ago_ts", current_ts - (HOURS*3600))
state.set_value("current_ts", current_ts)
state.set_value("one_period_ago_ts", one_period_ago_ts)

reached_end = True
while current_ts > one_period_ago_ts:
    item = pull_item(current_id)
    current_ts = item["time"]

    item = add_missing_fields(item)
    hn_data_import.write(item)
    current_id -= 1

    if not state.should_continue():
        reached_end = False
        state.request_new_run()
        break

if reached_end:
    state.reset()
else:
    state.set_value("last_id", current_id)
