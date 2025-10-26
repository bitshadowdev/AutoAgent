import requests
import json
import time
from bs4 import BeautifulSoup

def scrape_all_quotes(args: dict) -> dict:
    """Scrapea todas las citas de https://quotes.toscrape.com y guarda en quotes.json.
    Retorna dict con 'ok', 'file_path', 'count' y 'error' (si lo hubiere).
    """
    base_url = 'https://quotes.toscrape.com'
    next_page = '/'
    quotes = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; scraping-bot/1.0; +https://example.com/bot)'
    }
    try:
        while next_page:
            url = base_url + next_page
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
            except requests.exceptions.RequestException as e:
                return {'ok': False, 'error': f'Error al solicitar {url}: {str(e)}'}
            soup = BeautifulSoup(resp.text, 'html.parser')
            quote_divs = soup.select('div.quote')
            for div in quote_divs:
                text = div.select_one('span.text').get_text(strip=True)
                author = div.select_one('small.author').get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in div.select('div.tags a.tag')]
                quotes.append({'text': text, 'author': author, 'tags': tags})
            # buscar enlace a la siguiente página
            next_btn = soup.select_one('li.next > a')
            next_page = next_btn['href'] if next_btn else None
            time.sleep(1)  # respeto al servidor
        # Guardar en JSON
        file_path = 'quotes.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(quotes, f, ensure_ascii=False, indent=2)
        # Validar archivo creado
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list) and all(
                isinstance(item, dict) and
                {'text', 'author', 'tags'}.issubset(item.keys())
                for item in data):
                return {'ok': True, 'file_path': file_path, 'count': len(data)}
            else:
                return {'ok': False, 'error': 'El contenido del archivo no tiene el formato esperado'}
        except Exception as e:
            return {'ok': False, 'error': f'Error al validar el archivo JSON: {str(e)}'}
    except Exception as e:
        return {'ok': False, 'error': f'Error inesperado: {str(e)}'}