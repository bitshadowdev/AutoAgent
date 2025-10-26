import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_html(args: dict) -> dict:
    """Scrapea la página principal de Books to Scrape y genera un HTML con los libros.
    Args:
        args: {
            "url": "https://books.toscrape.com/",
            "output_path": "books.html"
        }
    Returns:
        dict con key 'ok' (bool) y, si ok, 'output_path' con la ruta absoluta del archivo generado; si falla, 'error'.
    """
    url = args.get("url")
    output_path = args.get("output_path")
    # 1. Descargar página
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Error al descargar la URL: {e}"}
    # 2. Parsear HTML y extraer datos
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        books = []
        for article in soup.select("article.product_pod"):
            title_tag = article.select_one("h3 a")
            title = title_tag["title"] if title_tag else "N/A"
            link = title_tag["href"] if title_tag else "#"
            link = requests.compat.urljoin(url, link)
            price_tag = article.select_one("p.price_color")
            price = price_tag.get_text().strip() if price_tag else "N/A"
            books.append({"title": title, "price": price, "link": link})
        # 3. Generar HTML
        html = """<!DOCTYPE html>
<html lang='es'>
<head>
<meta charset='UTF-8'>
<title>Books to Scrape</title>
<style>
    table{border-collapse:collapse;width:100%;}
    th,td{border:1px solid #ddd;padding:8px;}
    th{background-color:#f2f2f2;}
    tr:hover{background-color:#f9f9f9;}
</style>
</head>
<body>
<h1>Lista de libros de Books to Scrape</h1>
<table>
<thead><tr><th>Título</th><th>Precio</th><th>Enlace</th></tr></thead>
<tbody>
"""
        for b in books:
            html += f"<tr><td>{b['title']}</td><td>{b['price']}</td><td><a href='{b['link']}' target='_blank'>Ver</a></td></tr>\n"
        html += """</tbody></table>\n</body>\n</html>"""
        # 4. Guardar archivo
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return {"ok": True, "output_path": os.path.abspath(output_path)}
    except Exception as e:
        return {"ok": False, "error": f"Error procesando datos: {e}"}
