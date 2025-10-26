import requests
import time

def search_hackathon_ia_chile(args: dict) -> dict:
    """Busca hackathons de IA en Chile con lógica de fallback.

    Parámetros (args):
        Ninguno requerido.
    
    Retorna un dict con:
        - ok (bool): True si la búsqueda se realizó sin errores.
        - results (list): Lista de resultados (máx 5) con 'title' y 'url'.
        - message (str, opcional): Mensaje informativo cuando no hay resultados.
        - debug (list): Registro de cada intento (query, status_code, num_results).
    """
    base_url = "https://duckduckgo.com/"
    headers = {"Accept": "application/json"}
    # consultas inicial y de respaldo
    queries = [
        "hackathon agentes IA Chile",
        "hackathon IA Chile 2024",
        "evento agentes de inteligencia artificial Chile",
        "competencia IA Chile"
    ]
    debug_log = []
    results = []
    for q in queries:
        try:
            params = {"q": q, "format": "json", "pretty": "1", "no_html": "1", "skip_disambig": "1"}
            resp = requests.get(base_url, params=params, headers=headers, timeout=10)
            debug_log.append({"query": q, "status_code": resp.status_code})
            if resp.status_code != 200:
                # si es 202 esperar y reintentar una vez
                if resp.status_code == 202:
                    time.sleep(2)
                    resp = requests.get(base_url, params=params, headers=headers, timeout=10)
                    debug_log[-1]["retry_status_code"] = resp.status_code
                else:
                    continue
            data = resp.json()
            # DuckDuckGo devuelve resultados bajo la clave 'Results' o similar; usamos lo disponible
            raw = data.get('Results') or data.get('results') or []
            # Normalizamos los campos
            for item in raw:
                title = item.get('Text') or item.get('Title') or "Sin título"
                url = item.get('FirstURL') or item.get('Url') or "Sin URL"
                results.append({"title": title, "url": url})
            debug_log[-1]["num_results"] = len(raw)
            if results:
                break  # obtenidos resultados, salir del bucle
        except Exception as e:
            debug_log.append({"query": q, "error": str(e)})
            continue
    if results:
        return {"ok": True, "results": results[:5], "debug": debug_log}
    else:
        return {"ok": True, "results": [], "message": "No se encontraron resultados para su consulta.", "debug": debug_log}
