import requests
import json
from bs4 import BeautifulSoup
from pathlib import Path

def scrape_quotes(args: dict) -> dict:
    """
    Scrapea todas las citas de http://quotes.toscrape.com/ y las guarda en un archivo JSON.
    Argumentos opcionales en args:
        - url: URL base a scrapear (por defecto la página de ejemplo).
        - output_path: ruta del archivo JSON de salida (por defecto 'quotes.json' en el directorio actual).
    Retorna un dict con 'ok' y 'output_path' o 'error'.
    """
    url = args.get('url', 'http://quotes.toscrape.com/')
    output_path = args.get('output_path', 'quotes.json')
    try:
        quotes = []
        page = 1
        while True:
            resp = requests.get(url if page == 1 else f"{url.rstrip('/')}/page/{page}/")
            if resp.status_code != 200:
                break
            soup = BeautifulSoup(resp.text, 'html.parser')
            quote_elements = soup.select('.quote')
            if not quote_elements:
                break
            for el in quote_elements:
                text = el.select_one('.text').get_text(strip=True)
                author = el.select_one('.author').get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in el.select('.tags .tag')]
                quotes.append({
                    'text': text,
                    'author': author,
                    'tags': tags
                })
            page += 1
        # Guardar en JSON
        out_file = Path(output_path)
        out_file.write_text(json.dumps(quotes, ensure_ascii=False, indent=2))
        return {'ok': True, 'output_path': str(out_file)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}