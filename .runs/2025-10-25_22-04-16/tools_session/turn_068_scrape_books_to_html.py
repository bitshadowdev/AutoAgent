import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_html(args: dict) -> dict:
    """Descarga la página principal de books.toscrape.com, extrae título, precio y enlace de cada libro
    y genera un archivo HTML con una tabla de resultados.
    Parámetros esperados en *args*:
        - url (str): URL a scrapearear (por ejemplo, 'https://books.toscrape.com/')
        - output_path (str): ruta del archivo HTML a crear.
    Devuelve dict con {'ok': True, 'output_path': ...} o {'ok': False, 'error': ...}.
    """
    try:
        url = args.get('url')
        output_path = args.get('output_path')
        if not url or not output_path:
            return {'ok': False, 'error': 'Faltan parámetros url u output_path'}
        # Descargar la página
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        # Parsear HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        books = []
        for article in soup.select('article.product_pod'):
            # Título
            a_tag = article.select_one('h3 a')
            title = a_tag['title'].strip() if a_tag and a_tag.has_attr('title') else 'Sin título'
            # Enlace (relativo)
            link = a_tag['href'] if a_tag and a_tag.has_attr('href') else '#'
            # Convertir a URL absoluta
            link = requests.compat.urljoin(url, link)
            # Precio
            price_tag = article.select_one('p.price_color')
            price = price_tag.text.strip() if price_tag else 'N/A'
            books.append({'title': title, 'price': price, 'link': link})
        # Construir tabla HTML
        html = ['<!DOCTYPE html>', '<html lang="en">', '<head>', '<meta charset="UTF-8">',
                '<title>Books to Scrape - Lista</title>',
                '<style>',
                'table {border-collapse: collapse; width: 100%;}',
                'th, td {border: 1px solid #ddd; padding: 8px;}',
                'th {background-color: #f2f2f2; text-align: left;}',
                'tr:hover {background-color: #f5f5f5;}',
                '</style>', '</head>', '<body>',
                '<h1>Books to Scrape</h1>',
                '<table>', '<tr><th>Título</th><th>Precio</th><th>Enlace</th></tr>']
        for b in books:
            html.append(f"<tr><td>{b['title']}</td><td>{b['price']}</td><td><a href='{b['link']}' target='_blank'>Ver libro</a></td></tr>")
        html.extend(['</table>', '</body>', '</html>'])
        # Escribir archivo
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))
        if os.path.isfile(output_path):
            return {'ok': True, 'output_path': os.path.abspath(output_path)}
        else:
            return {'ok': False, 'error': 'Archivo no creado'}
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error de red: {e}'}
    except Exception as e:
        return {'ok': False, 'error': f'Excepción inesperada: {e}'}