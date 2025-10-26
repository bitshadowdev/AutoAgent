import requests
import json

def get_ai_news(args: dict) -> dict:
    """
    Consulta la API de SerpAPI para obtener noticias recientes sobre inteligencia artificial.
    Args:
        args (dict): Debe contener la clave 'api_key' con la API key de SerpAPI.
    Returns:
        dict: {'ok': True, 'news': [{'title': ..., 'link': ...}, ...]}
              o {'ok': False, 'error': 'mensaje'} en caso de falla.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'Falta la api_key en los argumentos.'}
        # Parámetros de búsqueda
        params = {
            'engine': 'google_news',
            'q': 'inteligencia artificial',
            'hl': 'es',
            'gl': 'es',
            'api_key': api_key,
            'num': '10'  # número de resultados
        }
        response = requests.get('https://serpapi.com/search.json', params=params, timeout=15)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error HTTP {response.status_code}: {response.text}'}
        data = response.json()
        # La respuesta contiene una lista bajo la clave 'news_results'
        news_items = data.get('news_results', [])
        news_list = []
        for item in news_items:
            title = item.get('title')
            link = item.get('link')
            if title and link:
                news_list.append({'title': title, 'link': link})
        return {'ok': True, 'news': news_list}
    except Exception as e:
        return {'ok': False, 'error': str(e)}