import requests
from bs4 import BeautifulSoup
import os

def scrape_books_to_scrape(args: dict) -> dict:
    """Scrapea la página principal de http://books.toscrape.com/ y guarda el HTML resultante.
    Args:
        args: dict con la clave 'output_path' indicando la ruta del archivo de salida.
    Returns:
        dict con claves 'ok' (bool), 'error' (str opcional), 'output_path' y 'test_passed' (bool).
    """
    output_path = args.get('output_path')
    if not output_path:
        return {"ok": False, "error": "Missing 'output_path' argument"}
    url = "http://books.toscrape.com/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {"ok": False, "error": f"Unexpected status code {response.status_code}"}
        html = response.text
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Network error: {str(e)}"}
    # Parsear para validar contenido básico
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Verificar que exista al menos un elemento de libro (ej. <article class="product_pod">)
        if not soup.select('article.product_pod') and not soup.select('li'):
            # No se encontró contenido esperado, pero continuamos guardando
            pass
    except Exception as e:
        return {"ok": False, "error": f"Parsing error: {str(e)}"}
    # Guardar archivo con UTF-8
    try:
        # Asegurarse de que el directorio exista
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        return {"ok": False, "error": f"File write error: {str(e)}"}
    # Prueba rápida de contenido
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            saved_html = f.read()
        test_passed = bool(soup.select('article.product_pod') or soup.select('li'))
    except Exception as e:
        return {"ok": False, "error": f"Test read error: {str(e)}"}
    return {"ok": True, "output_path": output_path, "test_passed": test_passed}
