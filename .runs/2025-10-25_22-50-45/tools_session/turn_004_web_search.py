import requests
import json

def web_search(args: dict) -> dict:
    """Busca información en la web usando la API pública de DuckDuckGo.

    Parámetros obligatorios:
      - query (str): cadena de búsqueda no vacía.

    Retorna un diccionario JSON‑serializable con:
      - ok (bool): True si la búsqueda fue exitosa.
      - results (list): lista de los resultados relevantes (título, URL y descripción).
      - error (str, opcional): mensaje de error si ok es False.
    """
    try:
        # validar parámetro
        query = args.get('query')
        if not isinstance(query, str) or not query.strip():
            return {"ok": False, "error": "El parámetro 'query' es obligatorio y no puede estar vacío."}
        query = query.strip()
        # llamada a la API de DuckDuckGo
        url = 'https://api.duckduckgo.com/'
        params = {
            'q': query,
            'format': 'json',
            'no_redirect': '1',
            'no_html': '1',
            'skip_disambig': '1'
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return {"ok": False, "error": f"Error HTTP {resp.status_code} al consultar la API."}
        data = resp.json()
        results = []
        # Preferir Abstract si existe
        abstract = data.get('AbstractText')
        if abstract:
            results.append({
                'title': data.get('Heading', query),
                'url': data.get('AbstractURL', ''),
                'description': abstract
            })
        # Añadir RelatedTopics (primeros 5)
        for topic in data.get('RelatedTopics', [])[:5]:
            if 'Text' in topic and 'FirstURL' in topic:
                results.append({
                    'title': topic.get('Text').split(' - ')[0],
                    'url': topic.get('FirstURL'),
                    'description': topic.get('Text')
                })
        if not results:
            return {"ok": False, "error": "No se encontraron resultados para la consulta."}
        return {"ok": True, "results": results}
    except Exception as e:
        return {"ok": False, "error": f"Excepción inesperada: {str(e)}"}
