import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_html(args: dict) -> dict:
    """Descarga la página principal de https://books.toscrape.com, extrae título, precio y enlace de cada libro
    y genera un archivo HTML con una tabla de resultados.
    Args:
        args: {'url': str, 'output_path': str}
    Returns:
        dict con claves 'ok' (bool) y 'output_path' o 'error'.
    """
    url = args.get('url')
    output_path = args.get('output_path')
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Error al descargar la página: {e}"}

    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        books = []
        for article in soup.select('article.product_pod'):
            a_tag = article.select_one('h3 a')
            title = a_tag.get('title', '').strip()
            link = a_tag.get('href', '').strip()
            # Convertir enlace relativo a absoluto
            link = requests.compat.urljoin(url, link)
            price_tag = article.select_one('p.price_color')
            price = price_tag.text.strip() if price_tag else ''
            books.append({"title": title, "price": price, "link": link})
    except Exception as e:
        return {"ok": False, "error": f"Error al parsear el HTML: {e}"}

    # Generar tabla HTML
    html_content = """<!DOCTYPE html>
<html lang='es'>
<head>
<meta charset='UTF-8'>
<title>Listado de libros de books.toscrape.com</title>
<style>
  table {border-collapse: collapse; width: 100%;}
  th, td {border: 1px solid #ddd; padding: 8px;}
  th {background-color: #f2f2f2; text-align: left;}
  tr:hover {background-color: #f9f9f9;}
</style>
</head>
<body>
<h1>Libros de books.toscrape.com</h1>
<table>
  <tr><th>Título</th><th>Precio</th><th>Enlace</th></tr>
"""
    for b in books:
        html_content += f"  <tr><td>{b['title']}</td><td>{b['price']}</td><td><a href='{b['link']}' target='_blank'>Ver</a></td></tr>\n"
    html_content += """</table>
</body>
</html>"""

    try:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
        return {"ok": False, "error": f"Error al escribir el archivo HTML: {e}"}

    return {"ok": True, "output_path": output_path}
