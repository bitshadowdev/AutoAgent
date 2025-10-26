import requests

def fetch_ai_news(args: dict) -> dict:
    """Obtiene las últimas noticias de Google News sobre inteligencia artificial usando SerpAPI.
    Argumentos esperados:
        args['api_key'] (str): clave de la API de SerpAPI.
        args.get('query', str): término de búsqueda (por defecto 'artificial intelligence').
        args.get('num', int): número máximo de resultados (por defecto 10).
    Retorna un dict con la lista de noticias bajo la clave 'news'. Cada noticia contiene:
        title, link, snippet, source, date.
    """
    api_key = args.get('api_key')
    if not api_key:
        return {'error': 'api_key is required'}
    query = args.get('query', 'artificial intelligence')
    num = args.get('num', 10)
    params = {
        'engine': 'google_news',
        'q': query,
        'hl': 'en',
        'gl': 'us',
        'api_key': api_key,
        'num': num
    }
    try:
        response = requests.get('https://serpapi.com/search', params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        # La respuesta tiene una clave 'news_results' con la lista de noticias.
        news_items = []
        for item in data.get('news_results', [])[:num]:
            news_items.append({
                'title': item.get('title'),
                'link': item.get('link'),
                'snippet': item.get('snippet'),
                'source': item.get('source'),
                'date': item.get('date')
            })
        return {'news': news_items}
    except Exception as e:
        return {'error': str(e)}