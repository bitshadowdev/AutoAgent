import requests
import time

def web_search(args: dict) -> dict:
    """Busca información en la web usando la API de DuckDuckGo.

    Parámetros:
        args (dict): Debe contener la clave 'query' con la cadena a buscar.
            - query (str): término de búsqueda, no puede estar vacío.

    Retorna:
        dict: {
            'ok': bool,
            'results': list de dict (solo si ok es True),
            'error': str (solo si ok es False)
        }
    """
    try:
        query = args.get('query', '')
        if not isinstance(query, str) or not query.strip():
            return {'ok': False, 'error': "El parámetro 'query' es obligatorio y no puede estar vacío."}
        query = query.strip()
        url = 'https://api.duckduckgo.com/'
        params = {
            'q': query,
            'format': 'json',
            'no_redirect': 1,
            'no_html': 1,
            'skip_disambig': 1
        }
        headers = {
            'Accept': 'application/json'
        }
        max_retries = 3
        for attempt in range(max_retries + 1):
            response = requests.get(url, params=params, headers=headers, timeout=10)
            status = response.status_code
            if status == 200:
                data = response.json()
                # Extraemos los "RelatedTopics" que contienen resultados útiles
                results = []
                for item in data.get('RelatedTopics', []):
                    if 'Text' in item and 'FirstURL' in item:
                        results.append({'title': item.get('Text'), 'url': item.get('FirstURL')})
                return {'ok': True, 'results': results[:10]}  # limitamos a 10 resultados
            elif status == 202:
                # 202 = aceptado pero todavía procesando; esperamos y reintentamos
                if attempt < max_retries:
                    time.sleep(1)  # espera breve antes de reintentar
                    continue
                else:
                    return {'ok': False, 'error': f"Respuesta 202 persistente después de {max_retries} reintentos."}
            else:
                return {'ok': False, 'error': f"Error HTTP {status} al consultar la API: {response.text}"}
    except requests.RequestException as e:
        return {'ok': False, 'error': f"Excepción de red al realizar la búsqueda: {str(e)}"}
    except Exception as e:
        return {'ok': False, 'error': f"Error inesperado: {str(e)}"}