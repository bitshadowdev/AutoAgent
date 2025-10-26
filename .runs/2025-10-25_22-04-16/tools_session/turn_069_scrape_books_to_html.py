import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_html(args: dict) -> dict:
    """Scrapea la página principal de books.toscrape.com y genera un HTML con título, precio y enlace de cada libro.
    Args:
        args: {
            "url": str,            # URL a scrape
            "output_path": str      # Ruta del archivo HTML a crear
        }
    Returns:
        dict con claves 'ok' (bool) y, si ok=True, 'output_path' y 'message';
        si ok=False, 'error' con descripción.
    """
    url = args.get('url')
    output_path = args.get('output_path')
    if not url or not output_path:
        return {'ok': False, 'error': 'Parámetros "url" y "output_path" son requeridos.'}
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error al descargar la página: {e}'}
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        books = soup.select('article.product_pod')
        rows = []
        for book in books:
            # título
            title_tag = book.h3.a
            title = title_tag.get('title', '').strip()
            # enlace relativo -> absoluto
            rel_link = title_tag.get('href', '')
            if rel_link.startswith('http'):
                link = rel_link
            else:
                # asegurar una barra entre base y relativo
                base = url.rstrip('/')
                link = f"{base}/{rel_link.lstrip('/')}"
            # precio
            price_tag = book.select_one('p.price_color')
            price = price_tag.text.strip() if price_tag else ''
            rows.append((title, price, link))
        # construir HTML
        html = """<html><head><meta charset='utf-8'><title>Books from books.toscrape.com</title></head><body>"""
        html += "<h1>Books from books.toscrape.com</h1>"
        html += "<table border='1' cellpadding='5' cellspacing='0'>"
        html += "<tr><th>Title</th><th>Price</th><th>Link</th></tr>"
        for title, price, link in rows:
            html += f"<tr><td>{title}</td><td>{price}</td><td><a href='{link}' target='_blank'>Link</a></td></tr>"
        html += "</table></body></html>"
        # escribir archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return {'ok': True, 'output_path': output_path, 'message': f'HTML guardado en {output_path}'}
    except Exception as e:
        return {'ok': False, 'error': f'Error al procesar datos: {e}'}