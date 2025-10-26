import requests
import json
from bs4 import BeautifulSoup
from pathlib import Path

def scrape_quotes(args: dict) -> dict:
    """Scrapea todas las citas de https://quotes.toscrape.com/ y las guarda en un JSON.
    Retorna un diccionario con el resultado.
    """
    base_url = 'https://quotes.toscrape.com'
    page_url = base_url + '/'
    quotes = []
    try:
        while True:
            resp = requests.get(page_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            for quote_div in soup.select('div.quote'):
                text = quote_div.select_one('span.text')
                author = quote_div.select_one('small.author')
                tags = [tag.get_text(strip=True) for tag in quote_div.select('div.tags a.tag')]
                quotes.append({
                    'text': text.get_text(strip=True) if text else '',
                    'author': author.get_text(strip=True) if author else '',
                    'tags': tags
                })
            # buscar enlace a la siguiente página
            next_link = soup.select_one('li.next a')
            if next_link and next_link.get('href'):
                page_url = base_url + next_link['href']
            else:
                break
        # guardar en archivo JSON
        output_path = Path('quotes.json')
        output_path.write_text(json.dumps(quotes, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'ok': True, 'path': str(output_path.resolve()), 'count': len(quotes)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}