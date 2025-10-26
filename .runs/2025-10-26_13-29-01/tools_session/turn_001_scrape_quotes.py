import requests
from bs4 import BeautifulSoup
import json

def scrape_quotes(args: dict) -> dict:
    """
    Scrapea todas las citas de http://quotes.toscrape.com y devuelve una lista de diccionarios.
    Cada diccionario contiene:
        - text: el texto de la cita
        - author: autor de la cita
        - tags: lista de etiquetas asociadas
    Retorna un dict con la clave 'ok' y, si es True, la clave 'quotes' con la lista.
    """
    base_url = args.get('base_url', 'http://quotes.toscrape.com')
    page = 1
    all_quotes = []
    try:
        while True:
            url = f"{base_url}/page/{page}/"
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                break
            soup = BeautifulSoup(resp.text, 'html.parser')
            quote_elements = soup.select('div.quote')
            if not quote_elements:
                break
            for q in quote_elements:
                text = q.select_one('span.text').get_text(strip=True)
                author = q.select_one('small.author').get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in q.select('div.tags a.tag')]
                all_quotes.append({
                    'text': text,
                    'author': author,
                    'tags': tags
                })
            # comprobar si hay enlace 'Next'
            next_btn = soup.select_one('li.next a')
            if not next_btn:
                break
            page += 1
        # opcional: guardar en archivo JSON
        json_path = 'quotes.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_quotes, f, ensure_ascii=False, indent=2)
        return {'ok': True, 'quotes': all_quotes, 'saved_to': json_path}
    except Exception as e:
        return {'ok': False, 'error': str(e)}