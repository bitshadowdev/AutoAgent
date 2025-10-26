import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_html(args: dict) -> dict:
    """Descarga la página principal de books.toscrape.com, extrae título, precio y enlace de cada libro y genera un HTML.
    Args:
        args: {
            'url': str,            # URL base (e.g., 'https://books.toscrape.com/')
            'output_path': str      # Ruta donde se guardará el HTML resultante
        }
    Returns:
        dict con 'ok': bool y 'message' o 'error'.
    """
    url = args.get('url')
    output_path = args.get('output_path')
    if not url or not output_path:
        return {'ok': False, 'error': 'Faltan parámetros url o output_path'}
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error al obtener la página: {e}'}
    try:
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Cada libro está dentro de <article class="product_pod">
        books = soup.select('article.product_pod')
        rows = []
        for b in books:
            title_tag = b.h3.a
            title = title_tag['title'].strip() if title_tag and title_tag.has_attr('title') else 'Sin título'
            price_tag = b.select_one('p.price_color')
            price = price_tag.text.strip() if price_tag else 'Sin precio'
            link_tag = b.h3.a
            link = link_tag['href'] if link_tag and link_tag.has_attr('href') else '#'
            # Construir URL completa
            if not link.startswith('http'):
                link = requests.compat.urljoin(url, link)
            rows.append({'title': title, 'price': price, 'link': link})
        # Generar HTML
        html_parts = []
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html lang="es">')
        html_parts.append('<head><meta charset="UTF-8"><title>Books to Scrape</title>')
        html_parts.append('<style>table{border-collapse:collapse;width:100%;}th,td{border:1px solid #ddd;padding:8px;}th{background:#f2f2f2;}</style>')
        html_parts.append('</head><body>')
        html_parts.append('<h1>Listado de libros de books.toscrape.com</h1>')
        html_parts.append('<table>')
        html_parts.append('<tr><th>Título</th><th>Precio</th><th>Enlace</th></tr>')
        for r in rows:
            html_parts.append(f'<tr><td>{r["title"]}</td><td>{r["price"]}</td><td><a href=\"{r["link"]}\" target=\"_blank\">Abrir</a></td></tr>')
        html_parts.append('</table>')
        html_parts.append('</body></html>')
        html_content = '\n'.join(html_parts)
        # Asegurarse de que el directorio exista
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return {'ok': True, 'message': f'HTML generado en {output_path}'}
    except Exception as e:
        return {'ok': False, 'error': f'Error al procesar datos: {e}'}