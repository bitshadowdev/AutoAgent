def get_ai_news(args: dict) -> dict:
    """Obtiene las últimas noticias sobre "inteligencia artificial" usando la API de SerpAPI.
    Parámetros:
        args (dict): debe contener 'api_key' (str) con la clave de SerpAPI.
    Retorna:
        dict: {'ok': bool, ...}
    """
    import requests
    import json

    # Validar API key
    api_key = args.get('api_key')
    if not isinstance(api_key, str) or not api_key.strip():
        return {'ok': False, 'error': 'API key inválida'}

    # Parámetros de la consulta
    params = {
        "engine": "news",
        "q": "inteligencia artificial",
        "api_key": api_key,
        "hl": "es",
        "num": "10"
    }

    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error HTTP {response.status_code}: {response.text}'}
        data = response.json()
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error de red: {str(e)}'}
    except Exception as e:
        return {'ok': False, 'error': f'Error al procesar la respuesta: {str(e)}'}

    # Extraer resultados de noticias
    results = data.get('news_results', [])
    if not results:
        return {'ok': True, 'news': [], 'message': 'No se encontraron noticias recientes'}

    news_list = []
    for item in results:
        news_list.append({
            'title': item.get('title'),
            'link': item.get('link'),
            'source': item.get('source', {}).get('title') if isinstance(item.get('source'), dict) else item.get('source'),
            'snippet': item.get('snippet'),
            'date': item.get('date')
        })

    return {'ok': True, 'news': news_list}
