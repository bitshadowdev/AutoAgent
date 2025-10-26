import requests
import json
import os
from bs4 import BeautifulSoup

def scrape_all_quotes(args: dict) -> dict:
    """Scrapea todas las citas de https://quotes.toscrape.com y las guarda en un JSON.
    Args:
        args: diccionario opcional que puede contener 'output_path' (ruta del archivo).
    Returns:
        dict con 'ok': bool y datos adicionales o mensaje de error.
    """
    output_path = args.get('output_path', 'quotes.json')
    base_url = 'https://quotes.toscrape.com'
    page_url = f"{base_url}/page/1/"
    all_quotes = []
    try:
        while True:
            resp = requests.get(page_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            quote_divs = soup.select('div.quote')
            for div in quote_divs:
                text = div.select_one('span.text').get_text(strip=True)
                author = div.select_one('small.author').get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in div.select('div.tags a.tag')]
                all_quotes.append({
                    'text': text,
                    'author': author,
                    'tags': tags
                })
            next_li = soup.select_one('li.next a')
            if not next_li:
                break
            next_href = next_li['href']
            page_url = f"{base_url}{next_href}"
        # Guardar en archivo JSON
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_quotes, f, ensure_ascii=False, indent=2)
        # Verificar que el archivo sea JSON válido
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        if not isinstance(loaded, list):
            raise ValueError('El contenido del archivo no es una lista JSON')
        return {'ok': True, 'file_path': os.path.abspath(output_path), 'count': len(loaded)}
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error de red: {str(e)}'}
    except (IOError, OSError) as e:
        return {'ok': False, 'error': f'Error de I/O: {str(e)}'}
    except Exception as e:
        return {'ok': False, 'error': f'Error inesperado: {str(e)}'}
