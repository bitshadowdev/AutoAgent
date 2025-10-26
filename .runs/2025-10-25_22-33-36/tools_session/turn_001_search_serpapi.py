import requests
import json

def search_serpapi(args: dict) -> dict:
    """Realiza una búsqueda en Google mediante SerpAPI.
    Args:
        args (dict): Debe contener la clave 'query' con la cadena a buscar.
    Returns:
        dict: {'ok': True, 'results': [...]} o {'ok': False, 'error': <mensaje>}
    """
    api_key = 'c7f9ec50307100bea7733ae460878f220dd13b6341bd6b6b225eab62a8001878'
    query = args.get('query', '')
    if not query:
        return {'ok': False, 'error': 'No se proporcionó la consulta.'}
    params = {
        'engine': 'google',
        'q': query,
        'api_key': api_key,
        'hl': 'es',
        'gl': 'ar',
        'num': '10'
    }
    try:
        response = requests.get('https://serpapi.com/search.json', params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Extraer resultados orgánicos relevantes
        organic = data.get('organic_results', [])
        results = []
        for item in organic:
            title = item.get('title')
            snippet = item.get('snippet')
            link = item.get('link')
            results.append({'title': title, 'snippet': snippet, 'link': link})
        return {'ok': True, 'results': results}
    except Exception as e:
        return {'ok': False, 'error': str(e)}