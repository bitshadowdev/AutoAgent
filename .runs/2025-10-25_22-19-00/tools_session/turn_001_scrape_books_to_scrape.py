import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json

def scrape_books_to_scrape(args: dict) -> dict:
    """Scrapea la página principal de http://books.toscrape.com, extrae información de los libros y genera un archivo HTML.
    Args:
        args: dict con la clave 'output_path' (ruta donde guardar el HTML).
    Returns:
        dict con 'ok' (bool), 'output_path' (str) y opcionalmente 'error' (str).
    """
    try:
        base_url = "http://books.toscrape.com/"
        response = requests.get(base_url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Cada libro está dentro de <article class="product_pod">
        books = []
        for article in soup.select('article.product_pod'):
            # Título
            title_tag = article.h3.a
            title = title_tag['title'].strip()
            # Precio
            price_tag = article.select_one('p.price_color')
            price = price_tag.text.strip() if price_tag else ''
            # Rating (clase como 'star-rating Three')
            rating_tag = article.select_one('p.star-rating')
            rating = rating_tag['class'][1] if rating_tag and len(rating_tag['class']) > 1 else 'Zero'
            # Enlace al detalle del libro (relativo)
            link_tag = article.h3.a
            relative_link = link_tag['href']
            # Normalizar enlace quitando rutas relativas "../"
            link = base_url + relative_link.replace('../', '')
            books.append({
                'title': title,
                'price': price,
                'rating': rating,
                'link': link
            })
        # Generar HTML
        html_parts = []
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html lang="en">')
        html_parts.append('<head><meta charset="UTF-8"><title>Books to Scrape - Listado</title>')
        html_parts.append('<style>table{border-collapse:collapse;width:100%;}th,td{border:1px solid #ddd;padding:8px;}th{background:#f2f2f2;}</style>')
        html_parts.append('</head><body>')
        html_parts.append('<h1>Listado de libros de Books to Scrape</h1>')
        html_parts.append('<table>')
        html_parts.append('<tr><th>Título</th><th>Precio</th><th>Rating</th><th>Enlace</th></tr>')
        for b in books:
            html_parts.append(
                f"<tr><td>{b['title']}</td><td>{b['price']}</td><td>{b['rating']}</td><td><a href='{b['link']}' target='_blank'>Ver</a></td></tr>"
            )
        html_parts.append('</table>')
        html_parts.append('</body></html>')
        html_content = "\n".join(html_parts)
        # Ruta de salida
        output_path = args.get('output_path', 'books.html')
        # Asegurarse de que el directorio exista
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(html_content, encoding='utf-8')
        return {'ok': True, 'output_path': str(Path(output_path).resolve())}
    except Exception as e:
        return {'ok': False, 'error': str(e)}