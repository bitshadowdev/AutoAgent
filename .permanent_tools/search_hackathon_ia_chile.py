import json

def search_hackathon_ia_chile(args: dict) -> dict:
    """Busca información sobre hackathons de agentes de IA en Chile.
    
    Parámetros:
        args (dict): No se requieren parámetros de entrada.
    
    Retorna:
        dict: {
            'ok': bool,
            'message': str,          # mensaje para el usuario
            'results': list,         # lista de resultados (máx 5) con 'title' y 'url'
            'debug_log': list        # información de depuración
        }
    """
    # Lista de consultas a intentar, desde la original a variantes de fallback
    queries = [
        "hackathon agentes IA Chile",
        "hackathon IA Chile 2024",
        "evento agentes de inteligencia artificial Chile",
        "competencia IA Chile"
    ]
    debug_log = []
    final_results = []
    try:
        for q in queries:
            # llamada a la herramienta existente web_search
            response = web_search({"query": q})
            debug_log.append({
                "query": q,
                "response_ok": response.get("ok", False),
                "num_results": len(response.get("results", []))
            })
            if response.get("ok") and response.get("results"):
                final_results = response["results"]
                break  # se encontró al menos un resultado
        if final_results:
            top_five = final_results[:5]
            formatted = []
            for r in top_five:
                title = r.get("title", "Sin título")
                url = r.get("url", "Sin URL")
                formatted.append({"title": title, "url": url})
            return {
                "ok": True,
                "message": "Se encontraron resultados para la búsqueda de hackathons de IA en Chile.",
                "results": formatted,
                "debug_log": debug_log
            }
        else:
            return {
                "ok": False,
                "message": "No se encontraron resultados para su consulta. ¿Desea refinar la búsqueda o proporcionar más detalles?",
                "results": [],
                "debug_log": debug_log
            }
    except Exception as e:
        return {
            "ok": False,
            "message": f"Error al ejecutar la búsqueda: {str(e)}",
            "results": [],
            "debug_log": debug_log
        }
