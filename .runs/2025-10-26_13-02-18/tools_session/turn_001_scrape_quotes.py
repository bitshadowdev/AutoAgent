import requests
from bs4 import BeautifulSoup

def scrape_quotes(args: dict) -> dict:
    """Scrapea todas las citas de http://quotes.toscrape.com.
    Devuelve un dict con la clave 'ok' (bool) y, si ok=True, la clave 'quotes' que es una lista de
    { 'text': str, 'author': str, 'tags': list[str] }.
    En caso de error, devuelve {'ok': False, 'error': mensaje}.
    """
    base_url = "http://quotes.toscrape.com"
    quotes = []
    try:
        page = 1
        while True:
            url = f"{base_url}/page/{page}/"
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                # Si la página no existe (404) terminamos
                break
            soup = BeautifulSoup(resp.text, "html.parser")
            quote_divs = soup.select("div.quote")
            if not quote_divs:
                break
            for div in quote_divs:
                text = div.select_one("span.text").get_text(strip=True).strip('“”')
                author = div.select_one("small.author").get_text(strip=True)
                tag_elements = div.select("div.tags a.tag")
                tags = [t.get_text(strip=True) for t in tag_elements]
                quotes.append({"text": text, "author": author, "tags": tags})
            page += 1
        return {"ok": True, "quotes": quotes}
    except Exception as e:
        return {"ok": False, "error": str(e)}