import requests
import time
import json
import os
from bs4 import BeautifulSoup

def scrape_all_quotes(args: dict) -> dict:
    """Extrae todas las citas de https://quotes.toscrape.com y las guarda en 'quotes.json'.
    Args:
        args (dict): No se utilizan argumentos, se mantiene por compatibilidad.
    Returns:
        dict: { 'ok': bool, 'count': int, 'file': str, 'error': str (opcional) }
    """
    base_url = 'https://quotes.toscrape.com'
    url = base_url
    all_quotes = []
    session = requests.Session()
    max_retries = 3
    backoff_delays = [1, 2, 4]

    while url:
        # --- petición con reintentos ---
        for attempt in range(max_retries):
            try:
                resp = session.get(url, timeout=10)
                resp.raise_for_status()
                break  # éxito, salir del bucle de reintentos
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    return {'ok': False, 'error': f'Error al descargar {url}: {e}'}
                time.sleep(backoff_delays[attempt])
        # --- parsear contenido ---
        soup = BeautifulSoup(resp.text, 'html.parser')
        quote_tags = soup.select('div.quote')
        for tag in quote_tags:
            text_tag = tag.select_one('span.text')
            author_tag = tag.select_one('small.author')
            if not text_tag or not author_tag:
                # registro de cita incompleta, se omite
                continue
            quote = {
                'text': text_tag.get_text(strip=True),
                'author': author_tag.get_text(strip=True)
            }
            # validar que los campos existan y no estén vacíos
            if quote['text'] and quote['author']:
                all_quotes.append(quote)
        # --- buscar enlace 'Next' ---
        next_link = soup.select_one('li.next > a')
        if next_link and next_link.get('href'):
            url = base_url.rstrip('/') + next_link['href']
        else:
            url = None
    # --- guardar en archivo JSON ---
    try:
        json_str = json.dumps(all_quotes, ensure_ascii=False, indent=2)
        file_path = os.path.abspath('quotes.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
    except Exception as e:
        return {'ok': False, 'error': f'Error al escribir el archivo JSON: {e}'}
    return {'ok': True, 'count': len(all_quotes), 'file': file_path}
