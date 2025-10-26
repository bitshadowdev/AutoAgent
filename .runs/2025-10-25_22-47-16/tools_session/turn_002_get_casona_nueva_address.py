import requests
from bs4 import BeautifulSoup

def get_casona_nueva_address(args: dict) -> dict:
    """Devuelve la dirección de la Casona Nueva en Santiago de Chile.
    Args: dict (no se usan parámetros)
    Returns: dict con {'ok': bool, 'address': str (si ok), 'error': str (si no ok)}
    """
    try:
        # Intentar obtener la página de Wikipedia en español
        url = "https://es.wikipedia.org/wiki/Casona_Nueva"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            infobox = soup.find("table", {"class": "infobox"})
            if infobox:
                for tr in infobox.find_all("tr"):
                    th = tr.find("th")
                    if th and "Dirección" in th.get_text():
                        td = tr.find("td")
                        if td:
                            address = td.get_text(separator=" ", strip=True)
                            return {"ok": True, "address": address}
        # Si no se encontró o no existe la página, realizar una búsqueda rápida en DuckDuckGo
        search_url = "https://duckduckgo.com/html/"
        params = {"q": "Casona Nueva Santiago de Chile dirección"}
        search_resp = requests.get(search_url, params=params, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if search_resp.status_code == 200:
            soup = BeautifulSoup(search_resp.text, "html.parser")
            results = soup.select("a.result__a")
            for a in results[:5]:
                snippet = a.get_text(strip=True)
                # Intentar extraer una dirección del snippet usando un patrón simple
                import re
                match = re.search(r"\d{1,5}\s+\w+(?:\s+\w+)*,\s*Santiago", snippet)
                if match:
                    return {"ok": True, "address": match.group(0)}
        return {"ok": False, "error": "No se encontró la dirección en Wikipedia ni en la búsqueda."}
    except Exception as e:
        return {"ok": False, "error": str(e)}