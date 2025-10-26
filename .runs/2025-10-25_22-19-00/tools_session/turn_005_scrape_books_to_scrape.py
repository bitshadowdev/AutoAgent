import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_scrape(args: dict) -> dict:
    """Scrapea la página principal de http://books.toscrape.com/ y guarda los libros en un HTML.
    Args:
        args: {'output_path': str}
    Returns:
        dict con 'ok' y, si es True, 'output_path'. En caso de error, 'ok': False y 'error'.
    """
    output_path = args.get('output_path')
    if not output_path:
        return {"ok": False, "error": "output_path no especificado en args"}
    url = 'http://books.toscrape.com/'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Error de red al obtener {url}: {e}"}
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        books = soup.select('article.product_pod')
        if not books:
            return {"ok": False, "error": "No se encontraron libros en la página"}
        # construir HTML sencillo
        html_parts = ["<html><head><meta charset='utf-8'><title>Books to Scrape</title></head><body>", "<h1>Lista de libros</h1>", "<ul>"]
        for book in books:
            # título
            title_tag = book.select_one('h3 a')
            title = title_tag['title'] if title_tag and title_tag.has_attr('title') else 'Sin título'
            # precio
            price_tag = book.select_one('p.price_color')
            price = price_tag.get_text(strip=True) if price_tag else 'Sin precio'
            # imagen
            img_tag = book.select_one('div.image_container img')
            img_src = img_tag['src'] if img_tag and img_tag.has_attr('src') else ''
            # la URL de la imagen es relativa
            img_url = requests.compat.urljoin(url, img_src)
            html_parts.append(
                f"<li><article><h2>{title}</h2><p>Precio: {price}</p><img src='{img_url}' alt='{title}'/></article></li>"
            )
        html_parts.extend(["</ul></body></html>"])
        html_content = "\n".join(html_parts)
        # escribir archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        # verificación rápida
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if '<article' not in content and '<li' not in content:
                raise ValueError('El archivo generado no contiene etiquetas de libro esperadas')
        except Exception as e:
            return {"ok": False, "error": f"Error tras escribir el archivo: {e}"}
        return {"ok": True, "output_path": os.path.abspath(output_path)}
    except Exception as e:
        return {"ok": False, "error": f"Error al procesar la página: {e}"}
