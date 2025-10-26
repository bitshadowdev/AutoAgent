import requests
import os
from bs4 import BeautifulSoup

def scrape_books_to_html(args: dict) -> dict:
    """Scrapea https://books.toscrape.com/ y guarda los datos en un archivo HTML.
    Args:
        args: dict con claves:
            - url (str): URL a scrappear (ej. 'https://books.toscrape.com/')
            - output_path (str): Ruta del archivo HTML a crear.
    Returns:
        dict con {'ok': bool, 'output_path': str, 'error': str (opcional)}
    """
    url = args.get('url')
    output_path = args.get('output_path')
    if not url or not output_path:
        return {'ok': False, 'error': 'Faltan parámetros necesarios: url y output_path'}
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error al descargar la página: {e}'}
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        books = []
        for article in soup.select('article.product_pod'):
            title_tag = article.select_one('h3 a')
            title = title_tag.get('title', '').strip()
            link = title_tag.get('href', '').strip()
            # Convertir enlace relativo a absoluto
            link = requests.compat.urljoin(url, link)
            price_tag = article.select_one('p.price_color')
            price = price_tag.text.strip() if price_tag else ''
            books.append({'title': title, 'price': price, 'link': link})
    except Exception as e:
        return {'ok': False, 'error': f'Error al parsear el HTML: {e}'}
    # Construir HTML
    html_rows = []
    for b in books:
        row = f"<tr><td><a href='{b['link']}' target='_blank'>{b['title']}</a></td><td>{b['price']}</td></tr>"
        html_rows.append(row)
    html_content = f"""
<!DOCTYPE html>
<html lang='es'>
<head>
    <meta charset='UTF-8'>
    <title>Books to Scrape - Lista de libros</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; }}
        th {{ background-color: #f2f2f2; text-align: left; }}
        tr:hover {{ background-color: #fafafa; }}
    </style>
</head>
<body>
    <h1>Books to Scrape – Resultados</h1>
    <table>
        <thead>
            <tr><th>Título</th><th>Precio</th></tr>
        </thead>
        <tbody>
            {''.join(html_rows)}
        </tbody>
    </table>
</body>
</html>
"""
    try:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
        return {'ok': False, 'error': f'Error al escribir el archivo HTML: {e}'}
    return {'ok': True, 'output_path': os.path.abspath(output_path)}