import requests
from bs4 import BeautifulSoup
from typing import Dict

HEADERS: Dict[str, str] = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

COOKIES: Dict[str, str] = {
    'session-id': '000-0000000-0000000',
    'ubid-main': '000-0000000-0000000',
    'lc-main': 'en_US'
}

URL = "https://www.imdb.com/chart/top/"

response = requests.get(URL, headers=HEADERS, cookies=COOKIES)
response.raise_for_status()

soup = BeautifulSoup(response.content, "html.parser")
with open("imdb_top_250.html", "w", encoding="utf-8") as file:
    file.write(soup.prettify())
