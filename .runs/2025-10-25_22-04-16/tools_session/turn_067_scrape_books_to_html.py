import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_html(args):
    """Scrapea la página principal de books.toscrape.com y guarda los datos en un archivo HTML.
    Args:
        args (dict): {
            'url': str,            # URL a scrapear (e.g., 'https://books.toscrape.com/')
            'output_path': str      # Ruta del archivo HTML a generar
        }
    Returns:
        dict: {'ok': True, 'output_path': str} o {'ok': False, 'error': str}
    """
    url = args.get('url')
    output_path = args.get('output_path')
    if not url or not output_path:
        return {'ok': False, 'error': 'Missing url or output_path'}
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Network error: {e}'}
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        books = soup.select('article.product_pod')
        rows = []
        for book in books:
            title_tag = book.select_one('h3 a')
            title = title_tag['title'] if title_tag and title_tag.has_attr('title') else 'Sin título'
            link = title_tag['href'] if title_tag and title_tag.has_attr('href') else '#'
            # Convertir enlace relativo a absoluto
            link = os.path.join(url, link) if not link.startswith('http') else link
            price_tag = book.select_one('p.price_color')
            price = price_tag.get_text().strip() if price_tag else 'N/A'
            rows.append({'title': title, 'price': price, 'link': link})
        # Construir HTML
        html_parts = []
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html lang="en">')
        html_parts.append('<head>')
        html_parts.append('<meta charset="UTF-8">')
        html_parts.append('<title>Books to Scrape - Listado</title>')
        html_parts.append('<style>')
        html_parts.append('table {border-collapse: collapse; width: 100%;}')
        html_parts.append('th, td {border: 1px solid #ddd; padding: 8px; text-align: left;}')
        html_parts.append('th {background-color: #f2f2f2;}')
        html_parts.append('tr:hover {background-color: #f9f9f9;}')
        html_parts.append('a {color: #1a0dab; text-decoration: none;}')
        html_parts.append('</style>')
        html_parts.append('</head>')
        html_parts.append('<body>')
        html_parts.append('<h1>Books to Scrape - Listado de libros</h1>')
        html_parts.append('<table>')
        html_parts.append('<thead><tr><th>Título</th><th>Precio</th><th>Enlace</th></tr></thead>')
        html_parts.append('<tbody>')
        for row in rows:
            html_parts.append(f"<tr><td>{row['title']}</td><td>{row['price']}</td><td><a href='{row['link']}' target='_blank'>Ver</a></td></tr>")
        html_parts.append('</tbody></table>')
        html_parts.append('</body></html>')
        html_content = '\n'.join(html_parts)
        # Guardar archivo
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return {'ok': True, 'output_path': os.path.abspath(output_path)}
    except Exception as e:
        return {'ok': False, 'error': f'Parsing or writing error: {e}'}
