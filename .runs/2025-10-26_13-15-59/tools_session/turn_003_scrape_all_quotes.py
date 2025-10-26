import requests, time, json, os
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

def scrape_all_quotes(args: dict) -> dict:
    """Extrae todas las citas de https://quotes.toscrape.com y las guarda en quotes.json.
    Devuelve un diccionario con el estado de la operación.
    """
    base_url = "https://quotes.toscrape.com"
    url = base_url
    quotes = []
    max_retries = 3
    backoff_delays = [1, 2, 4]

    while url:
        # ---------- intento de descarga con backoff ----------
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                break
            except RequestException as exc:
                if attempt == max_retries - 1:
                    return {"ok": False, "error": f"Error al descargar {url}: {exc}"}
                time.sleep(backoff_delays[attempt])
        # ---------- parseo del HTML ----------
        soup = BeautifulSoup(response.text, "html.parser")
        for quote_tag in soup.select('.quote'):
            text_el = quote_tag.select_one('.text')
            author_el = quote_tag.select_one('.author')
            if text_el is None or author_el is None:
                # Entrada incompleta, se ignora
                continue
            quotes.append({
                "text": text_el.get_text(strip=True),
                "author": author_el.get_text(strip=True)
            })
        # ---------- buscar enlace 'Next' ----------
        next_link = soup.select_one('li.next > a')
        if next_link and next_link.get('href'):
            # la página siguiente es relativa a base_url
            url = base_url.rstrip('/') + next_link['href']
        else:
            url = None

    # ---------- escritura del JSON ----------
    json_path = os.path.abspath('quotes.json')
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(quotes, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        return {"ok": False, "error": f"Error al escribir el archivo JSON: {exc}"}

    return {"ok": True, "file": json_path, "count": len(quotes)}
