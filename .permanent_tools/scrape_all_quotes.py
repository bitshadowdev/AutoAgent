import requests
import json
import os
from pathlib import Path
from bs4 import BeautifulSoup

def scrape_all_quotes(args: dict) -> dict:
    """Scrapea todas las citas de https://quotes.toscrape.com/ y las guarda en 'quotes.json'.
    Args puede contener opcionalmente:
        - 'output_path': ruta completa o relativa del archivo JSON a crear (por defecto 'quotes.json').
    Retorna un dict con:
        - ok (bool): True si todo salió bien.
        - file_path (str): ruta del archivo creado.
        - total (int): número total de citas extraídas.
        - message (str): mensaje descriptivo.
        - error (str, opcional): descripción del error en caso de fallo.
    """
    base_url = "https://quotes.toscrape.com"
    page_url = base_url + "/"
    all_quotes = []
    try:
        while True:
            resp = requests.get(page_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            quote_divs = soup.select("div.quote")
            for div in quote_divs:
                text = div.select_one("span.text")
                author = div.select_one("small.author")
                tag_elements = div.select("div.tags a.tag")
                quote_data = {
                    "text": text.get_text(strip=True) if text else "",
                    "author": author.get_text(strip=True) if author else "",
                    "tags": [t.get_text(strip=True) for t in tag_elements]
                }
                all_quotes.append(quote_data)
            # buscar enlace a la siguiente página
            next_btn = soup.select_one("li.next a")
            if next_btn and next_btn.get('href'):
                page_url = base_url + next_btn['href']
            else:
                break
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Error de red al obtener {page_url}: {e}"}

    # determinar ruta de salida
    output_path = args.get("output_path", "quotes.json")
    try:
        # asegurarse de que el directorio exista
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        # escribir JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_quotes, f, ensure_ascii=False, indent=2)
    except (IOError, OSError) as e:
        return {"ok": False, "error": f"Error al escribir el archivo {output_path}: {e}"}

    # verificar existencia y tamaño
    try:
        file_path_obj = Path(output_path)
        if not file_path_obj.is_file():
            return {"ok": False, "error": f"El archivo {output_path} no se encontró después de intentar guardarlo."}
        size = file_path_obj.stat().st_size
        if size == 0:
            return {"ok": False, "error": f"El archivo {output_path} está vacío."}
    except Exception as e:
        return {"ok": False, "error": f"Error al verificar el archivo {output_path}: {e}"}

    return {
        "ok": True,
        "file_path": str(file_path_obj.resolve()),
        "total": len(all_quotes),
        "message": f"Se guardaron correctamente {len(all_quotes)} citas en {file_path_obj.resolve()}."
    }