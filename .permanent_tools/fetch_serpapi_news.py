import requests

def fetch_serpapi_news(args):
    """
    Consulta la API de SerpAPI para obtener resultados de noticias de Google.
    Args:
        args (dict): { 'api_key': str, 'query': str, 'num': int }
    Returns:
        dict: {'results': [{'title': str, 'link': str, 'source': str, 'snippet': str, 'date': str}, ...]}
    """
    api_key = args.get('api_key')
    query = args.get('query')
    num = args.get('num', 10)
    if not api_key or not query:
        return {'error': 'api_key y query son obligatorios'}
    params = {
        'engine': 'google_news',
        'q': query,
        'api_key': api_key,
        'num': num
    }
    try:
        response = requests.get('https://serpapi.com/search.json', params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        news = []
        for entry in data.get('news_results', []):
            news.append({
                'title': entry.get('title'),
                'link': entry.get('link'),
                'source': entry.get('source'),
                'snippet': entry.get('snippet'),
                'date': entry.get('date')
            })
        return {'results': news}
    except Exception as e:
        return {'error': str(e)}