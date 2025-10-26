import requests
from bs4 import BeautifulSoup
import json

def scrape_quotes(args: dict) -> dict:
    """
    Scrapea todas las citas de http://quotes.toscrape.com
    y devuelve una lista de diccionarios con los campos:
      - text: el texto de la cita
      - author: nombre del autor
      - tags: lista de etiquetas
    """
    base_url = 'http://quotes.toscrape.com'
    page = 1
    quotes = []
    try:
        while True:
            url = f"{base_url}/page/{page}/"
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                # No more pages (404) or error
                break
            soup = BeautifulSoup(resp.text, 'html.parser')
            quote_blocks = soup.select('.quote')
            if not quote_blocks:
                break
            for block in quote_blocks:
                text = block.select_one('.text').get_text(strip=True)
                author = block.select_one('.author').get_text(strip=True)
                tag_elements = block.select('.tags .tag')
                tags = [t.get_text(strip=True) for t in tag_elements]
                quotes.append({
                    'text': text,
                    'author': author,
                    'tags': tags
                })
            page += 1
        return {
            'ok': True,
            'data': quotes,
            'message': f'Scrape completed, {len(quotes)} quotes collected.'
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }