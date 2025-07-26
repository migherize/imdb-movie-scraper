import requests
from bs4 import BeautifulSoup

URL = "https://www.imdb.com/title/tt0111161/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(URL, headers=HEADERS)
soup = BeautifulSoup(response.text, "html.parser")

actor_tags = soup.select('a[data-testid="title-cast-item__actor"]')
main_actors = [a.text.strip() for a in actor_tags[:3]]

print("Actores principales:", main_actors)

metascore_tag = soup.find("span", class_="metacritic-score-box")

if metascore_tag:
    metascore = metascore_tag.text.strip()
    print("🎬 Metascore:", metascore)
else:
    print("❌ No se encontró Metascore en esta película.")
