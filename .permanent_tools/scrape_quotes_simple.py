def scrape_quotes_simple(args):
    import requests
    from bs4 import BeautifulSoup
    url = args.get('url')
    if not url:
        return {'ok': False, 'error': 'Falta la clave "url" en los argumentos.'}
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        return {'ok': False, 'error': f'Error al obtener la URL: {e}'}
    soup = BeautifulSoup(resp.text, 'html.parser')
    quotes_data = []
    for quote in soup.select('div.quote'):
        text_el = quote.select_one('span.text')
        author_el = quote.select_one('small.author')
        tags_el = quote.select('div.tags a.tag')
        text = text_el.get_text(strip=True) if text_el else ''
        author = author_el.get_text(strip=True) if author_el else ''
        tags = [t.get_text(strip=True) for t in tags_el] if tags_el else []
        quotes_data.append({'text': text, 'author': author, 'tags': tags})
    return {'ok': True, 'quotes': quotes_data}
