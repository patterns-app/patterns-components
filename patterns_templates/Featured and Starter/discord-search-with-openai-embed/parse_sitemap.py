from patterns import (
    Parameter,
    State,
    Table,
)
import requests

from bs4 import BeautifulSoup

sitemap_urls = Table('sitemap_urls', mode='w')

sitmap_url = Parameter("sitmap_url", type=str )

page = requests.get(sitmap_url)
xml = page.text

soup = BeautifulSoup(xml, "html.parser")

sitemap_urls.reset()

urls = soup.find_all('url')
for url in urls:
    url_string = url.loc.getText('', True)
    sitemap_urls.append({'url': url_string})

