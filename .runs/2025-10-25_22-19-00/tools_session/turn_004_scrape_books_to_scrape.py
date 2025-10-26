import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_scrape(args: dict) -> dict:
    """Scrape http://books.toscrape.com/ and write a simple HTML file.
    Expected args: {'output_path': 'ruta/al/archivo.html'}
    Returns a dict with 'ok' and optional error/message info.
    """
    url = "http://books.toscrape.com/"
    output_path = args.get('output_path', 'books.html')
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error al obtener la página: {e}'}

    if response.status_code != 200:
        return {'ok': False, 'error': f'Status code inesperado: {response.status_code}'}

    soup = BeautifulSoup(response.text, 'html.parser')
    books = []
    for article in soup.select('article.product_pod'):
        # título
        title_tag = article.h3.a
        title = title_tag.get('title', '').strip()
        # precio
        price_tag = article.select_one('p.price_color')
        price = price_tag.text.strip() if price_tag else ''
        # imagen
        img_tag = article.select_one('img')
        img_src = img_tag.get('src', '') if img_tag else ''
        # limpiar la ruta relativa (comienza con "../")
        img_url = img_src.replace('../', '')
        img_url = f'http://books.toscrape.com/{img_url}' if img_url else ''
        books.append({'title': title, 'price': price, 'img_url': img_url})

    # generar HTML simple
    html_parts = [
        '<!DOCTYPE html>',
        '<html>',
        '<head>',
        '<meta charset="utf-8">',
        '<title>Books to Scrape</title>',
        '</head>',
        '<body>',
        '<h1>Lista de libros</h1>',
        '<ul>'
    ]
    for b in books:
        html_parts.append(
            f"<li><h2>{b['title']}</h2><p>{b['price']}</p><img src='{b['img_url']}' alt='Portada'></li>"
        )
    html_parts.extend(['</ul>', '</body>', '</html>'])
    html_content = '\n'.join(html_parts)

    # asegurarse de que el directorio exista
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
        return {'ok': False, 'error': f'Error al escribir el archivo: {e}'}

    # verificación rápida del contenido
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if '<li>' not in content and '<article' not in content:
            return {'ok': False, 'error': 'El archivo HTML generado no contiene elementos de libro.'}
    except Exception as e:
        return {'ok': False, 'error': f'Error al leer el archivo para verificación: {e}'}

    return {'ok': True, 'output_path': output_path, 'message': f'Scrape completado, {len(books)} libros guardados.'}