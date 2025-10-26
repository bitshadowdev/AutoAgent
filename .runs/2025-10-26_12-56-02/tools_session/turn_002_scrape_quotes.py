import requests
import json
from bs4 import BeautifulSoup
from pathlib import Path

def scrape_quotes(args: dict) -> dict:
    """Descarga todas las citas del sitio quotes.toscrape.com y las guarda en 'quotes.json'.
    Retorna {'ok': True, 'path': <ruta>, 'count': <número de citas>} o {'ok': False, 'error': <msg>}.
    """
    base_url = 'http://quotes.toscrape.com'
    quotes = []
    try:
        page = 1
        while True:
            url = f"{base_url}/page/{page}/"
            resp = requests.get(url, timeout=10)
            # Forzar codificación UTF-8
            resp.encoding = 'utf-8'
            if resp.status_code != 200:
                break
            soup = BeautifulSoup(resp.text, 'html.parser')
            quote_divs = soup.select('div.quote')
            if not quote_divs:
                break
            for div in quote_divs:
                text = div.select_one('span.text').get_text(strip=True)
                author = div.select_one('small.author').get_text(strip=True)
                tags = [t.get_text(strip=True) for t in div.select('div.tags a.tag')]
                quotes.append({
                    'text': text,
                    'author': author,
                    'tags': tags
                })
            page += 1
        # Guardar en JSON con UTF-8 y sin escapar caracteres Unicode
        output_path = Path('quotes.json')
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(quotes, f, ensure_ascii=False, indent=2)
        # Verificación simple: intentar cargar el archivo
        with output_path.open('r', encoding='utf-8') as f:
            _ = json.load(f)
        return {'ok': True, 'path': str(output_path), 'count': len(quotes)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}