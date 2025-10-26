import requests
from bs4 import BeautifulSoup

def scrape_quotes(args: dict) -> dict:
    """Scrapea todas las citas del sitio https://quotes.toscrape.com/.
    Devuelve un dict con la clave 'quotes' que contiene una lista de objetos:
    {
        'text': str,
        'author': str,
        'tags': [str, ...]
    }
    En caso de error, retorna {'ok': False, 'error': <mensaje>}.
    """
    base_url = 'https://quotes.toscrape.com'
    page_url = '/'
    all_quotes = []
    try:
        while True:
            resp = requests.get(base_url + page_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            quote_elements = soup.select('div.quote')
            for qe in quote_elements:
                text = qe.select_one('span.text').get_text(strip=True)
                author = qe.select_one('small.author').get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in qe.select('div.tags a.tag')]
                all_quotes.append({'text': text, 'author': author, 'tags': tags})
            # buscar enlace a la siguiente página
            next_btn = soup.select_one('li.next a')
            if next_btn and next_btn.get('href'):
                page_url = next_btn['href']
            else:
                break
        return {'ok': True, 'quotes': all_quotes}
    except Exception as e:
        return {'ok': False, 'error': str(e)}