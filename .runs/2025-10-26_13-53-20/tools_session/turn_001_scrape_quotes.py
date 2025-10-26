import requests
from bs4 import BeautifulSoup

def scrape_quotes(args: dict) -> dict:
    """Scrapea todas las citas de http://quotes.toscrape.com y devuelve una lista de diccionarios.
    Cada diccionario contiene: 'text', 'author' y 'tags' (lista).
    Args puede contener opcionalmente 'url' para usar otro sitio similar.
    """
    try:
        base_url = args.get('url', 'http://quotes.toscrape.com')
        page_url = base_url
        quotes = []
        while page_url:
            resp = requests.get(page_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            quote_blocks = soup.select('div.quote')
            for block in quote_blocks:
                text = block.select_one('span.text').get_text(strip=True)
                author = block.select_one('small.author').get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in block.select('div.tags a.tag')]
                quotes.append({
                    'text': text,
                    'author': author,
                    'tags': tags
                })
            # buscar enlace a la siguiente página
            next_btn = soup.select_one('li.next a')
            if next_btn and next_btn.get('href'):
                page_url = base_url.rstrip('/') + next_btn['href']
            else:
                page_url = None
        return {'ok': True, 'quotes': quotes}
    except Exception as e:
        return {'ok': False, 'error': str(e)}