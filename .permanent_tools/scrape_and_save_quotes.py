import requests
import json
import os
import sys
from bs4 import BeautifulSoup

def scrape_and_save_quotes(args: dict) -> dict:
    """Scrapea todas las citas de quotes.toscrape.com y las guarda en un JSON.
    Parámetros en *args*:
        - base_url (str): URL base del sitio (p. ej. 'http://quotes.toscrape.com').
        - output_path (str, opcional): Ruta del archivo JSON donde se guardarán los datos.
    Retorna un dict con los resultados y mensajes de éxito/error.
    """
    base_url = args.get('base_url', 'http://quotes.toscrape.com')
    output_path = args.get('output_path', 'quotes.json')
    all_quotes = []
    next_page_url = base_url
    try:
        while next_page_url:
            resp = requests.get(next_page_url, timeout=10)
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
            # buscar enlace a la siguiente página
            next_link = soup.select_one('li.next a')
            if next_link and next_link.get('href'):
                next_page_url = base_url.rstrip('/') + next_link['href']
            else:
                next_page_url = None
    except Exception as e:
        return {'ok': False, 'error': f'Error al obtener datos del sitio: {e}'}

    # Guardar en disco
    try:
        # asegurarse de que el directorio exista
        os.makedirs(os.path.dirname(os.path.abspath(output_path)) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({'quotes': all_quotes}, f, ensure_ascii=False, indent=2)
    except OSError as e:
        return {'ok': False, 'error': f'Error al escribir el archivo: {e}'}

    # Verificar que el archivo se haya creado y contenga datos válidos
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict) or 'quotes' not in data:
            raise ValueError('Estructura de JSON inesperada')
    except Exception as e:
        return {'ok': False, 'error': f'Error al validar el archivo generado: {e}'}

    result = {
        'ok': True,
        'message': f'Scraping completado. {len(all_quotes)} citas guardadas en "{output_path}".',
        'output_path': output_path,
        'count': len(all_quotes)
    }
    return result

# Permitir ejecución directa como script CLI
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Scrapea quotes.toscrape.com y guarda en JSON')
    parser.add_argument('--base_url', default='http://quotes.toscrape.com', help='URL base del sitio a scrapear')
    parser.add_argument('--output', default='quotes.json', help='Ruta del archivo JSON de salida')
    args = parser.parse_args()
    result = scrape_and_save_quotes({'base_url': args.base_url, 'output_path': args.output})
    print(json.dumps(result, ensure_ascii=False, indent=2))
