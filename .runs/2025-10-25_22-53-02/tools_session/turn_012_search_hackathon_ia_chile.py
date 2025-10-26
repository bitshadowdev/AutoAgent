import time
import requests

def search_hackathon_ia_chile(args: dict) -> dict:
    """Busca hackathons de agentes de IA en Chile utilizando la API pública de DuckDuckGo.
    
    No requiere parámetros de entrada. Internamente prueba una lista de consultas
    alternativas y devuelve los primeros resultados no vacíos.
    
    Retorno:
        dict con claves:
            - ok (bool): indica si la operación tuvo éxito.
            - results (list): lista de dicts con 'title' y 'url' (si ok).
            - message (str): mensaje informativo en caso de no encontrar resultados.
    """
    queries = [
        "hackathon IA Chile",
        "hackathon inteligencia artificial Chile",
        "hackathon agentes IA Chile 2024",
        "evento IA Chile 2024",
        "competencia inteligencia artificial Chile",
        "hackathon AI agents Chile",
    ]
    endpoint = "https://api.duckduckgo.com/"
    headers = {"Accept": "application/json"}
    for q in queries:
        try:
            params = {"q": q, "format": "json", "no_redirect": 1, "no_html": 1, "skip_disambig": 1}
            response = requests.get(endpoint, params=params, headers=headers, timeout=10)
            if response.status_code == 202:
                # esperar y reintentar brevemente
                time.sleep(1)
                response = requests.get(endpoint, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                continue
            data = response.json()
            # DuckDuckGo devuelve resultados en 'RelatedTopics' (lista de dicts)
            results = []
            for item in data.get('RelatedTopics', []):
                if 'Text' in item and 'FirstURL' in item:
                    results.append({"title": item['Text'], "url": item['FirstURL']})
                # algunos items pueden contener 'Topics' anidados
                if 'Topics' in item:
                    for sub in item['Topics']:
                        if 'Text' in sub and 'FirstURL' in sub:
                            results.append({"title": sub['Text'], "url": sub['FirstURL']})
            if results:
                return {"ok": True, "results": results}
        except Exception as e:
            # registrar error y continuar con la siguiente consulta
            continue
    # si llegó aquí, no encontró resultados
    return {"ok": False, "message": "No se encontraron resultados para hackathons de IA en Chile con las consultas probadas."}
