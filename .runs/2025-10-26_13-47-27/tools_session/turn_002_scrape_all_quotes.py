import requests
import json
import sys
import subprocess

# asegurar que BeautifulSoup está disponible
try:
    from bs4 import BeautifulSoup
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'beautifulsoup4'])
    from bs4 import BeautifulSoup

def scrape_all_quotes(args: dict) -> dict:
    """Scrapea todas las citas de http://quotes.toscrape.com/ y las guarda en JSON.
    Args:
        args: dict con opcionales:
            - base_url (str): URL inicial (default "http://quotes.toscrape.com/")
            - output_path (str): ruta del archivo JSON de salida (default "quotes_all.json")
    Returns:
        dict con claves 'ok', 'count', 'path' o 'error' en caso de fallo.
    """
    base_url = args.get('base_url', 'http://quotes.toscrape.com/')
    output_path = args.get('output_path', 'quotes_all.json')
    quotes = []
    url = base_url
    try:
        while url:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            for div in soup.select('.quote'):
                text = div.select_one('.text').get_text(strip=True)
                author = div.select_one('.author').get_text(strip=True)
                tags = [t.get_text(strip=True) for t in div.select('.tag')]
                quotes.append({'text': text, 'author': author, 'tags': tags})
            nxt = soup.select_one('.next > a')
            if nxt:
                next_href = nxt.get('href')
                url = requests.compat.urljoin(url, next_href)
            else:
                url = None
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Network error: {e}'}
    # escribir en archivo
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(quotes, f, ensure_ascii=False, indent=2)
    except IOError as e:
        return {'ok': False, 'error': f'File write error: {e}'}
    # validar JSON
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError('JSON root is not a list')
    except Exception as e:
        return {'ok': False, 'error': f'JSON validation error: {e}'}
    return {'ok': True, 'count': len(quotes), 'path': output_path}
