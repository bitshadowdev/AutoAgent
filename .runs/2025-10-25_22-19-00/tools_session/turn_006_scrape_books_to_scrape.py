import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_scrape(args):
    import traceback
    output_path = args.get('output_path', 'books.html')
    url = 'http://books.toscrape.com/'
    # ---------- petición HTTP ----------
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Error al obtener la página: {e}"}
    # ---------- parseado y extracción ----------
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        books = soup.select('article.product_pod')
        if not books:
            return {"ok": False, "error": "No se encontraron libros en la página."}
        # Construir HTML simple
        html_parts = [
            '<html>',
            '<head><meta charset="utf-8"><title>Books to Scrape</title></head>',
            '<body>',
            '<h1>Books</h1>',
            '<ul>'
        ]
        for b in books:
            title = b.h3.a['title']
            price = b.select_one('p.price_color').text.strip()
            img_rel = b.find('img')['src']
            img_url = url + img_rel.replace('../', '')
            html_parts.append(
                f'<li style="margin-bottom:15px;">'
                f'<img src="{img_url}" alt="{title}" style="height:100px;"/><br/>'
                f'{title}<br/>{price}'
                f'</li>'
            )
        html_parts.extend(['</ul>', '</body>', '</html>'])
        html_content = "\n".join(html_parts)
        # ---------- escritura del archivo ----------
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        # ---------- verificación rápida ----------
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if '<li' not in content:
                raise ValueError('El archivo generado no contiene elementos de libro.')
        except Exception as ve:
            return {"ok": False, "error": f"Verificación falló: {ve}"}
        return {"ok": True, "output_path": output_path, "message": "Scraping completado exitosamente."}
    except Exception as e:
        return {"ok": False, "error": f"Error de parsing o escritura: {e}", "traceback": traceback.format_exc()}
