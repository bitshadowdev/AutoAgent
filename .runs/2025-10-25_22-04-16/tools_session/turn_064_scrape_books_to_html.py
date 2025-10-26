import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_html(args: dict) -> dict:
    """Descarga la página principal de https://books.toscrape.com/, extrae título, precio y enlace de cada libro y genera un archivo HTML.
    Args:
        args: dict con claves opcionales:
            url (str): URL base (por defecto la página principal).
            output_path (str): ruta del archivo HTML a crear (por defecto 'books.html').
    Returns:
        dict con claves:
            ok (bool): True si se completó con éxito.
            output_path (str): ruta del archivo generado.
            count (int): número de libros extraídos.
            error (str, opcional): mensaje de error si ok es False.
    """
    url = args.get('url', 'https://books.toscrape.com/')
    output_path = args.get('output_path', 'books.html')
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error al descargar la página: {e}'}
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Cada libro está en article.product_pod
        books = soup.select('article.product_pod')
        rows = []
        for book in books:
            title_tag = book.h3.a
            title = title_tag['title'].strip() if title_tag else 'Sin título'
            price_tag = book.select_one('p.price_color')
            price = price_tag.text.strip() if price_tag else 'Sin precio'
            link_tag = title_tag
            href = link_tag['href'] if link_tag else '#'
            # Convertir enlace relativo a absoluto
            link = requests.compat.urljoin(url, href)
            rows.append((title, price, link))
        # Generar HTML
        html = ['<!DOCTYPE html>', '<html>', '<head>', '<meta charset="utf-8">',
                '<title>Books to Scrape - Lista de libros</title>',
                '<style>',
                'table {border-collapse: collapse; width: 100%;}',
                'th, td {border: 1px solid #ddd; padding: 8px;}',
                'th {background-color: #f2f2f2; text-align: left;}',
                'tr:hover {background-color: #f5f5f5;}',
                '</style>', '</head>', '<body>',
                '<h1>Lista de libros de books.toscrape.com</h1>',
                '<table>',
                '<tr><th>Título</th><th>Precio</th><th>Enlace</th></tr>']
        for title, price, link in rows:
            html.append(f'<tr><td>{title}</td><td>{price}</td><td><a href="{link}" target="_blank">Ver</a></td></tr>')
        html.extend(['</table>', '</body>', '</html>'])
        html_content = '\n'.join(html)
        # Guardar archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        # Verificar que el archivo exista
        if not os.path.isfile(output_path):
            return {'ok': False, 'error': 'El archivo HTML no se creó correctamente.'}
        return {'ok': True, 'output_path': os.path.abspath(output_path), 'count': len(rows)}
    except Exception as e:
        return {'ok': False, 'error': f'Error procesando la página: {e}'}