import requests
import json
from bs4 import BeautifulSoup
from pathlib import Path

def scrape_quotes(args: dict) -> dict:
    """Raspa todas las citas del sitio quotes.toscrape.com y las guarda en un JSON.
    Args:
        args: dict opcional con clave 'url' (página inicial). Si no se provee, se usa la página principal.
    Returns:
        dict con 'ok' y, si es True, 'file_path' al JSON creado; si falla, 'error'."""
    try:
        base_url = args.get('url', 'http://quotes.toscrape.com/')
        quotes = []
        next_page = base_url
        while next_page:
            resp = requests.get(next_page, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            for quote_div in soup.select('div.quote'):
                text = quote_div.select_one('span.text').get_text(strip=True)
                author = quote_div.select_one('small.author').get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in quote_div.select('div.tags a.tag')]
                quotes.append({
                    'text': text,
                    'author': author,
                    'tags': tags
                })
            next_tag = soup.select_one('li.next a')
            if next_tag and next_tag.get('href'):
                next_page = requests.compat.urljoin(base_url, next_tag['href'])
            else:
                next_page = None
        # Guardar en JSON
        output_path = Path('quotes.json')
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(quotes, f, ensure_ascii=False, indent=2)
        return {'ok': True, 'file_path': str(output_path)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}