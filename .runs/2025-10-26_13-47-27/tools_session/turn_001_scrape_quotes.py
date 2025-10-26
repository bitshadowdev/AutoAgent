import requests
from bs4 import BeautifulSoup

def scrape_quotes(args: dict) -> dict:
    """Scrapea todas las citas de http://quotes.toscrape.com/.
    Devuelve un dict con la clave 'ok' (bool) y, si es True, la lista de citas bajo 'data'.
    Cada cita es un dict con 'text', 'author' y 'tags' (lista).
    En caso de error, devuelve {'ok': False, 'error': 'mensaje'}.
    """
    base_url = 'http://quotes.toscrape.com'
    page_url = '/'
    quotes = []
    try:
        while True:
            resp = requests.get(base_url + page_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            for quote_div in soup.select('div.quote'):
                text = quote_div.find('span', class_='text').get_text(strip=True)
                author = quote_div.find('small', class_='author').get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in quote_div.select('div.tags a.tag')]
                quotes.append({'text': text, 'author': author, 'tags': tags})
            # buscar enlace a la siguiente página
            next_btn = soup.select_one('li.next > a')
            if next_btn and 'href' in next_btn.attrs:
                page_url = next_btn['href']
            else:
                break
        return {'ok': True, 'data': quotes}
    except Exception as e:
        return {'ok': False, 'error': str(e)}