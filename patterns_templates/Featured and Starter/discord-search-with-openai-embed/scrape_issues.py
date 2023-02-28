from patterns import (
    Parameter,
    State,
    Table,
)
import requests
from bs4 import BeautifulSoup

github_repo_issues = Table("github_repo_issues", "r")
github_issues_text = Table('github_issues_text', mode='w')
github_issues_text.reset()

for record in github_repo_issues.read():
    url = record['url']

    strings = [record['title'], record['body']]

    page_number = 1
    read_all_pages = False

    while not read_all_pages:
        r = requests.get(f'{url}/comments?per_page=100&page={page_number}')

        data = r.json()
        for comment in data:
            strings.append(comment['body'].strip())

        if len(data) < 100:
            read_all_pages = True
        else:
            page_number += 1        

    filtered_strings = [s for s in strings if len(s) > 0]
    page_text = '. '.join(filtered_strings)
    record['text'] = '. '.join(filtered_strings)
    github_issues_text.append(record)

