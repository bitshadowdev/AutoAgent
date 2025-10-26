import requests
import urllib.parse

def web_search(args: dict) -> dict:
    """Busca información en la web mediante la API JSON de DuckDuckGo.

    Parámetros esperados en *args*:
        - query (str): la cadena de búsqueda.

    Retorna un diccionario JSON‑serializable con:
        - ok (bool): True si la búsqueda tuvo éxito.
        - results (list): lista de resultados (título y URL).
        - error (str, opcional): mensaje de error si ok es False.
    """
    try:
        query = args.get('query')
        if not query:
            return {'ok': False, 'error': 'Falta el parámetro "query"'}
        # Codificar la consulta para la URL
        encoded_query = urllib.parse.quote_plus(query)
        url = (
            f"https://api.duckduckgo.com/?q={encoded_query}"
            "&format=json&no_redirect=1&no_html=1&skip_disambig=1"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Extraer resultados relevantes de la sección "RelatedTopics"
        results = []
        for item in data.get('RelatedTopics', []):
            # Algunos ítems pueden ser grupos con sub‑items
            if 'Text' in item and 'FirstURL' in item:
                results.append({'title': item['Text'], 'url': item['FirstURL']})
            elif 'Topics' in item:
                for sub in item['Topics']:
                    if 'Text' in sub and 'FirstURL' in sub:
                        results.append({'title': sub['Text'], 'url': sub['FirstURL']})
        # Limitar a los primeros 10 resultados para mantener la respuesta breve
        results = results[:10]
        return {'ok': True, 'results': results}
    except Exception as e:
        return {'ok': False, 'error': str(e)}