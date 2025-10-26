import requests
from bs4 import BeautifulSoup

def scrape_quotes(args: dict) -> dict:
    """Scrapea todas las páginas de https://quotes.toscrape.com y devuelve una lista de citas.
    Cada cita es un dict con los campos 'text' y 'author'.
    Args:
        args: dict vacío o con clave 'url' opcional.
    Returns:
        dict con claves 'ok' (bool) y 'data' (list de citas) o 'error' (str).
    """
    base_url = args.get('url', 'https://quotes.toscrape.com')
    quotes = []
    try:
        page = 1
        while True:
            resp = requests.get(f"{base_url}/page/{page}/")
            if resp.status_code != 200:
                break
            soup = BeautifulSoup(resp.text, 'html.parser')
            quote_divs = soup.select('div.quote')
            if not quote_divs:
                break
            for div in quote_divs:
                text = div.select_one('span.text').get_text(strip=True)
                author = div.select_one('small.author').get_text(strip=True)
                quotes.append({'text': text, 'author': author})
            # check if next page exists
            next_btn = soup.select_one('li.next > a')
            if not next_btn:
                break
            page += 1
        return {'ok': True, 'data': quotes}
    except Exception as e:
        return {'ok': False, 'error': str(e)}