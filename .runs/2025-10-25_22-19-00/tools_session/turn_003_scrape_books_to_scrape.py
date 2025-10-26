import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_scrape(args: dict) -> dict:
    """Scrapea la página principal de http://books.toscrape.com/ y guarda los libros en un HTML.
    Args:
        args: {'output_path': str}
    Returns:
        dict con 'ok': True/False y datos o mensaje de error.
    """
    output_path = args.get('output_path', 'books.html')
    url = 'http://books.toscrape.com/'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error al obtener la página: {e}'}

    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Los libros están en <article class="product_pod">
        books = soup.select('article.product_pod')
        if not books:
            return {'ok': False, 'error': 'No se encontraron libros en la página.'}
        # Construir contenido HTML
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="es">',
            '<head>',
            '<meta charset="UTF-8">',
            '<title>Books to Scrape</title>',
            '<style>',
            'body {font-family: Arial, sans-serif; margin: 20px;}',
            '.book {border: 1px solid #ddd; padding: 10px; margin-bottom: 10px;}',
            '.book img {max-width: 100px; display: block; margin-bottom: 5px;}',
            '</style>',
            '</head>',
            '<body>',
            '<h1>Lista de libros de Books to Scrape</h1>',
            '<ul>'
        ]
        for book in books:
            title = book.h3.a['title']
            price = book.select_one('p.price_color').text.strip()
            img_rel = book.find('img')['src']
            img_url = requests.compat.urljoin(url, img_rel)
            html_parts.append(
                f'<li class="book">'
                f'<img src="{img_url}" alt="{title}" />'
                f'<strong>{title}</strong><br/>'
                f'Precio: {price}'
                f'</li>'
            )
        html_parts.extend(['</ul>', '</body>', '</html>'])
        html_content = '\n'.join(html_parts)
        # Guardar archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
        return {'ok': False, 'error': f'Error durante el parsing o guardado: {e}'}

    # Verificación rápida del archivo generado
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            generated = f.read()
        if ('<li class="book"' not in generated) and ('<article' not in generated):
            return {'ok': False, 'error': 'El HTML generado no contiene entradas de libros.'}
    except Exception as e:
        return {'ok': False, 'error': f'Error al leer el archivo generado: {e}'}

    return {'ok': True, 'output_path': os.path.abspath(output_path), 'message': f'Scraping completado, archivo guardado en {output_path}'}