import requests
from bs4 import BeautifulSoup

def scrape_books_to_scrape(args: dict) -> dict:
    """Scrapea la página principal de http://books.toscrape.com/ y guarda
    la información de los libros en un archivo HTML.
    Args:
        args: dict con clave 'output_path' opcional.
    Returns:
        dict con 'ok' y datos adicionales o mensaje de error.
    """
    output_path = args.get('output_path', 'books.html')
    url = 'http://books.toscrape.com/'

    # ---------- solicitud HTTP ----------
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error de red: {e}'}

    # ---------- parseo HTML ----------
    soup = BeautifulSoup(response.text, 'html.parser')
    books = []
    for article in soup.select('article.product_pod'):
        try:
            title = article.h3.a['title']
            price = article.select_one('p.price_color').get_text(strip=True)
            img_rel = article.find('img')['src']
            img_url = requests.compat.urljoin(url, img_rel)
            books.append({'title': title, 'price': price, 'image': img_url})
        except Exception:
            # Ignorar libros con datos incompletos
            continue

    # ---------- generación de HTML ----------
    html = (
        '<!DOCTYPE html>'
        '<html><head><meta charset="utf-8"><title>Books to Scrape</title></head><body>'
        '<h1>Books to Scrape - Página principal</h1>'
        '<ul>'
    )
    for b in books:
        html += (
            f'<li><article>'
            f'<h2>{b["title"]}</h2>'
            f'<p>Precio: {b["price"]}</p>'
            f'<img src="{b["image"]}" alt="{b["title"]}">'
            f'</article></li>'
        )
    html += '</ul></body></html>'

    # ---------- escritura del archivo ----------
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    except Exception as e:
        return {'ok': False, 'error': f'Error al escribir el archivo: {e}'}

    # ---------- verificación rápida ----------
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if '<article' not in content:
            raise ValueError('El archivo generado no contiene ninguna etiqueta <article>')
    except Exception as e:
        return {'ok': False, 'error': f'Error de verificación: {e}'}

    return {'ok': True, 'output_path': output_path, 'books_extracted': len(books)}