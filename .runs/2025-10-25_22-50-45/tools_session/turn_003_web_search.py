import requests
import json

def web_search(args: dict) -> dict:
    """Buscar información en la web usando la API de DuckDuckGo.

    Parámetros requeridos (en `args`):
        - query (str): Término de búsqueda. No puede estar vacío.

    Resultado (dict):
        - ok (bool): True si la búsqueda tuvo éxito.
        - results (list): Lista de snippets de texto relevantes (máx. 5).
        - abstract (str): Resumen principal si está disponible.
        - error (str, opcional): Mensaje de error cuando ok es False.
    """
    try:
        query = args.get('query', '')
        if not isinstance(query, str) or not query.strip():
            return {"ok": False, "error": "El parámetro 'query' es obligatorio y no puede estar vacío."}
        # Preparar URL de la API
        url = 'https://api.duckduckgo.com/'
        params = {
            'q': query,
            'format': 'json',
            'no_html': 1,
            'skip_disambiguation': 1,
            't': 'agente_programador'
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return {"ok": False, "error": f"Error HTTP {resp.status_code} al contactar la API."}
        data = resp.json()
        # Obtener resumen abstracto
        abstract = data.get('AbstractText', '').strip()
        # Recopilar snippets de topics relacionados
        snippets = []
        for topic in data.get('RelatedTopics', []):
            if isinstance(topic, dict) and 'Text' in topic:
                snippets.append(topic['Text'])
            elif isinstance(topic, dict) and 'Topics' in topic:
                for sub in topic['Topics']:
                    if 'Text' in sub:
                        snippets.append(sub['Text'])
            if len(snippets) >= 5:
                break
        return {
            "ok": True,
            "abstract": abstract,
            "results": snippets[:5]
        }
    except Exception as e:
        return {"ok": False, "error": f"Excepción inesperada: {str(e)}"}
