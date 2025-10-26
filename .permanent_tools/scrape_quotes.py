import requests
import json
import os
from bs4 import BeautifulSoup

def scrape_quotes(args: dict) -> dict:
    """
    Scrapea todas las citas del sitio http://quotes.toscrape.com (todas sus páginas) y las guarda en un archivo JSON.
    Argumentos opcionales (en args):
        - output_path (str): ruta donde guardar el JSON. Si no se indica, se usa './quotes.json'.
    Retorna un dict con:
        - ok (bool): True si todo salió bien.
        - path (str): ruta al archivo JSON generado (si ok).
        - count (int): número de citas obtenidas.
        - error (str, opcional): mensaje de error en caso de fallo.
    """
    try:
        base_url = "http://quotes.toscrape.com"
        url = base_url
        quotes = []
        while True:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            quote_blocks = soup.select("div.quote")
            for block in quote_blocks:
                text = block.select_one("span.text").get_text(strip=True)
                author = block.select_one("small.author").get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in block.select("div.tags a.tag")]
                quotes.append({"text": text, "author": author, "tags": tags})
            # buscar enlace a la siguiente página
            next_btn = soup.select_one("li.next a")
            if not next_btn:
                break
            next_href = next_btn["href"]
            url = base_url + next_href
        # determinar ruta de salida
        output_path = args.get("output_path", "quotes.json")
        # asegurarse el directorio exista
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(quotes, f, ensure_ascii=False, indent=2)
        return {"ok": True, "path": os.path.abspath(output_path), "count": len(quotes)}
    except Exception as e:
        return {"ok": False, "error": str(e)}