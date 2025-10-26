import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_html(args: dict) -> dict:
    """Scrapea la página principal de Books to Scrape y genera un archivo HTML con los libros.
    Args:
        args: dict con opcional:
            - url (str): URL base del sitio (por defecto 'https://books.toscrape.com/')
            - output_path (str): ruta del archivo HTML a crear (por defecto 'books.html')
    Returns:
        dict con 'ok': bool, 'output_path': str y opcional 'error' en caso de fallo.
    """
    url = args.get('url', 'https://books.toscrape.com/')
    output_path = args.get('output_path', 'books.html')
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Obtener los contenedores de libros
        articles = soup.select('article.product_pod')
        books = []
        for art in articles:
            title = art.h3.a['title'].strip()
            price = art.select_one('p.price_color').text.strip()
            link = art.h3.a['href']
            # Normalizar enlace
            if not link.startswith('http'):
                link = os.path.join(url, link)
            books.append({'title': title, 'price': price, 'link': link})
        # Generar HTML
        html_parts = []
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html lang="en"><head><meta charset="UTF-8"><title>Books to Scrape</title>')
        html_parts.append('<style>table{border-collapse:collapse;width:100%;}th,td{border:1px solid #ddd;padding:8px;}th{background:#f2f2f2;}</style>')
        html_parts.append('</head><body>')
        html_parts.append('<h1>Books to Scrape - Lista de libros</h1>')
        html_parts.append('<table><tr><th>Título</th><th>Precio</th><th>Enlace</th></tr>')
        for b in books:
            html_parts.append(f"<tr><td>{b['title']}</td><td>{b['price']}</td><td><a href='{b['link']}' target='_blank'>Ver</a></td></tr>")
        html_parts.append('</table></body></html>')
        html_content = '\n'.join(html_parts)
        # Guardar archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return {'ok': True, 'output_path': os.path.abspath(output_path)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
