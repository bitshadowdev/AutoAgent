import requests
import json

def get_person_summary(args: dict) -> dict:
    """Consulta SerpAPI para obtener información de una persona y genera un resumen.
    Args:
        args: dict con claves:
            - query (str): término de búsqueda.
            - api_key (str): clave de SerpAPI.
    Returns:
        dict con claves:
            - ok (bool): True si se obtuvo información útil.
            - summary (str): párrafo con la descripción biográfica/profesional.
            - source_links (list): enlaces de los resultados usados.
            - error (str, opcional): mensaje de error en caso de fallo.
    """
    query = args.get('query')
    api_key = args.get('api_key')
    if not query or not api_key:
        return {"ok": False, "error": "Faltan 'query' o 'api_key' en los argumentos."}
    try:
        # Construir la URL de SerpAPI
        url = 'https://serpapi.com/search.json'
        params = {
            'engine': 'google',
            'q': query,
            'hl': 'es',
            'gl': 'cl',
            'api_key': api_key
        }
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return {"ok": False, "error": f"Código HTTP inesperado: {response.status_code}"}
        data = response.json()
        # Buscar resultados orgánicos (organic_results) o knowledge graph (knowledge_graph)
        results = []
        if 'knowledge_graph' in data:
            kg = data['knowledge_graph']
            # Convertir knowledge graph a formato similar a organic_results
            title = kg.get('title') or ''
            description = kg.get('description') or ''
            link = kg.get('url') or ''
            results.append({'title': title, 'snippet': description, 'link': link})
        if 'organic_results' in data:
            results.extend([
                {'title': r.get('title', ''), 'snippet': r.get('snippet', ''), 'link': r.get('link', '')}
                for r in data['organic_results']
            ])
        # Filtrar resultados que parezcan contener información biográfica o profesional
        bio_keywords = [
            'perfil', 'bio', 'biografía', 'currículum', 'experiencia', 'trabaja', 'profesión',
            'ingeniero', 'desarrollador', 'estudiante', 'colega', 'empresa', 'trabajo', 'LinkedIn',
            'Kaggle', 'Pinterest', 'GitHub'
        ]
        filtered = []
        for r in results:
            text = (r['title'] + ' ' + r['snippet']).lower()
            if any(kw.lower() in text for kw in bio_keywords):
                filtered.append(r)
        # Si no hay filtrados, usar los primeros 3 resultados como fallback
        if not filtered:
            filtered = results[:3]
        # Construir el resumen combinando snippets
        snippets = []
        links = []
        for r in filtered:
            snippet = r['snippet'].strip()
            if snippet:
                snippets.append(snippet)
                if r['link']:
                    links.append(r['link'])
        if not snippets:
            return {
                "ok": False,
                "summary": "Información no encontrada. Se sugiere buscar en fuentes como LinkedIn, Kaggle o redes sociales.",
                "source_links": []
            }
        # Crear un párrafo unificado (simple concatenación con separación)
        summary = ' '.join(snippets)
        # Limitar longitud razonable
        if len(summary) > 1000:
            summary = summary[:997] + '...'
        # Devolver resultado
        return {
            "ok": True,
            "summary": summary,
            "source_links": list(dict.fromkeys(links))  # eliminar duplicados manteniendo orden
        }
    except requests.RequestException as e:
        return {"ok": False, "error": f"Error de red: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"Excepción inesperada: {str(e)}"}
