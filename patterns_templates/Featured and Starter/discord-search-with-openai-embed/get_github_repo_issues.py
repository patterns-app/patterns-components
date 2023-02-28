from patterns import (
    Parameter,
    State,
    Table,
)
import requests

github_repo_issues_table = Table("github_repo_issues", "w")

github_token = Parameter('github_token', type=str)

github_owner_username = Parameter('github_owner_username', type=str)
github_repo_slug = Parameter('github_repo_slug', type=str)

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {github_token}"
}

github_repo_issues_table.reset()

read_all_pages = False
page_number = 1

while not read_all_pages:
    r = requests.get(f'https://api.github.com/repos/{github_owner_username}/{github_repo_slug}/issues?per_page=100&page={page_number}')

    data = r.json()
    for record in data:
        github_repo_issues_table.append(record)

    if len(data) < 100:
        read_all_pages = True
    else:
        page_number += 1
