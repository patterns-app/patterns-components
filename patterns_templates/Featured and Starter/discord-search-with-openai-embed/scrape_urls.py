from patterns import (
    Parameter,
    State,
    Table,
)
import requests
from bs4 import BeautifulSoup

sitemap_urls = Table("sitemap_urls", "r")
pages_texts = Table('pages_texts', mode='w')

stream = sitemap_urls.as_stream()
stream.rewind()
pages_texts.reset()

for record in stream.consume_records():
    url = record['url']
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Get the whole body tag
    tag = soup.body

    # Print each string recursively
    strings = [string.strip() for string in tag.strings]
    filtered_strings = [s for s in strings if len(s) > 0]
    page_text = '. '.join(filtered_strings)
    pages_texts.append({'url': url, 'page_text': page_text})

