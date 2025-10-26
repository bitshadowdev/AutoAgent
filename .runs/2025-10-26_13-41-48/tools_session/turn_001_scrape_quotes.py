import requests
from bs4 import BeautifulSoup
import json

def scrape_quotes(args: dict) -> dict:
    """Scrapea todas las citas de http://quotes.toscrape.com y devuelve una lista JSON.
    Cada elemento tiene: 'text', 'author' y 'tags'.
    """
    base_url = 'http://quotes.toscrape.com'
    url = base_url
    quotes = []
    try:
        while url:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            for quote in soup.select('.quote'):
                text = quote.select_one('.text').get_text(strip=True)
                author = quote.select_one('.author').get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in quote.select('.tags .tag')]
                quotes.append({
                    'text': text,
                    'author': author,
                    'tags': tags
                })
            next_btn = soup.select_one('li.next > a')
            if next_btn and next_btn.get('href'):
                url = base_url + next_btn['href']
            else:
                url = None
        return {'ok': True, 'data': quotes}
    except Exception as e:
        return {'ok': False, 'error': str(e)}