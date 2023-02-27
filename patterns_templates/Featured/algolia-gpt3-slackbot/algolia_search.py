from patterns import (
    Parameter,
    State,
    Table,
)

from algoliasearch.search_client import SearchClient

algolia_app = Parameter('algolia_app_id', description="Application Id")
algolia_api_key = Parameter('algolia_api_key', description="Search API key")
algolia_index = Parameter('algolia_index')


# Connect and authenticate with your Algolia app
client = SearchClient.create(algolia_app, algolia_api_key)

# Create a new index and add a record
index = client.init_index(algolia_index)

questions = Table('questions')
search_results = Table("search_results", "w")

content = []

for question in questions.as_stream().consume_records():
    # Search for the first question otherwise, just pass along the question
    searchResults = index.search(question['question'])
    for record in searchResults['hits']:
        if record['content'] is None:
            continue
        if record['anchor'] is None:
            continue
        record['question'] = question['question']
        record['slack_channel'] = question['slack_channel']
        record['thread'] = question['thread']
        record['ts'] = question['ts']
        content.append(record)

search_results.append(content)