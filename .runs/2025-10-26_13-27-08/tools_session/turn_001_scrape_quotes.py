import requests
from bs4 import BeautifulSoup
import json
import os

def scrape_quotes(args: dict) -> dict:
    """
    Scrapea todas las citas de http://quotes.toscrape.com/ y guarda el resultado en un archivo JSON.
    Args:
        args: diccionario vacío (no se requieren parámetros).
    Returns:
        dict con 'ok': bool, 'file_path': str (ruta del JSON creado) y 'error' opcional.
    """
    base_url = "http://quotes.toscrape.com"
    page_url = "/"
    all_quotes = []
    try:
        while True:
            resp = requests.get(base_url + page_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            quote_elements = soup.select("div.quote")
            for q in quote_elements:
                text = q.select_one("span.text").get_text(strip=True)
                author = q.select_one("small.author").get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in q.select("div.tags a.tag")]
                all_quotes.append({"text": text, "author": author, "tags": tags})
            # buscar enlace a página siguiente
            next_btn = soup.select_one("li.next a")
            if next_btn and next_btn.get('href'):
                page_url = next_btn['href']
            else:
                break
        # guardar a JSON
        output_path = os.path.abspath("quotes.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_quotes, f, ensure_ascii=False, indent=2)
        return {"ok": True, "file_path": output_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}