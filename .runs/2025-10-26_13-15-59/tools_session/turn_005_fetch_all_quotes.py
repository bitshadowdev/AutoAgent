import requests
import time
import json
from bs4 import BeautifulSoup

def fetch_all_quotes(args: dict) -> dict:
    base_url = 'https://quotes.toscrape.com'
    url = base_url
    all_quotes = []
    max_retries = 3
    backoff_delays = [1, 2, 4]
    while url:
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                break  # éxito, salir del bucle de reintentos
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    return {'ok': False, 'error': f'Error al obtener {url}: {e}'}
                time.sleep(backoff_delays[attempt])
        soup = BeautifulSoup(response.text, 'html.parser')
        quote_elements = soup.select('.quote')
        for q in quote_elements:
            text_el = q.select_one('.text')
            author_el = q.select_one('.author')
            if not text_el or not author_el:
                continue
            quote = {
                'text': text_el.get_text(strip=True),
                'author': author_el.get_text(strip=True)
            }
            all_quotes.append(quote)
        next_link = soup.select_one('li.next > a')
        if next_link and next_link.get('href'):
            url = base_url + next_link['href']
        else:
            url = None
    # Serializar y guardar en archivo JSON
    json_str = json.dumps(all_quotes, ensure_ascii=False, indent=2)
    file_path = 'quotes.json'
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
    except Exception as e:
        return {'ok': False, 'error': f'Error al escribir el archivo: {e}'}
    return {'ok': True, 'count': len(all_quotes), 'file': file_path, 'data': all_quotes}