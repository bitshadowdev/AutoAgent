import requests
import json

def get_ai_news(args: dict) -> dict:
    """Obtiene las últimas noticias sobre inteligencia artificial usando la API de SerpAPI.
    Args:
        args (dict): Debe contener la clave 'api_key' con la API key de SerpAPI.
    Returns:
        dict: {
            'ok': bool,
            'news': list of dict (título, link, source, snippet) opcional,
            'error': str opcional
        }
    """
    try:
        api_key = args.get('api_key', '').strip()
        if not api_key:
            return {'ok': False, 'error': 'API key no proporcionada o está vacía.'}

        # Parámetros de búsqueda en SerpAPI para noticias de Google sobre "inteligencia artificial"
        params = {
            'engine': 'google_news',
            'q': 'inteligencia artificial',
            'api_key': api_key,
            'hl': 'es',
            'gl': 'es',
            'num': '10'  # número máximo de resultados
        }
        url = 'https://serpapi.com/search.json'
        response = requests.get(url, params=params, timeout=15)

        if response.status_code != 200:
            # Manejo de errores comunes de la API
            if response.status_code == 401:
                err_msg = 'API key inválida o no autorizada (401).'
            elif response.status_code == 429:
                err_msg = 'Límite de peticiones excedido (429).'
            else:
                err_msg = f'Error HTTP inesperado: {response.status_code}.'
            return {'ok': False, 'error': err_msg}

        data = response.json()
        # SerpAPI devuelve la lista de noticias en la clave 'news_results'
        news_items = data.get('news_results', [])
        if not news_items:
            return {'ok': True, 'news': [], 'message': 'No se encontraron noticias.'}

        # Extraer campos relevantes
        news_list = []
        for item in news_items:
            news_entry = {
                'title': item.get('title'),
                'link': item.get('link'),
                'source': item.get('source'),
                'snippet': item.get('snippet')
            }
            news_list.append(news_entry)

        return {'ok': True, 'news': news_list}
    except requests.RequestException as e:
        return {'ok': False, 'error': f'Error de red al contactar la API: {str(e)}'}
    except json.JSONDecodeError:
        return {'ok': False, 'error': 'Respuesta de la API no es JSON válido.'}
    except Exception as e:
        return {'ok': False, 'error': f'Error inesperado: {str(e)}'}