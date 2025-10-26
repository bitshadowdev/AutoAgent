import requests
import json

def get_person_summary(args: dict) -> dict:
    """Obtiene y sintetiza información biográfica de una persona usando SerpAPI.

    Parámetros en *args*:
        - query (str): nombre a buscar.
        - api_key (str): clave de SerpAPI.
    Retorna dict con:
        - ok (bool): indica éxito.
        - summary (str): párrafo biográfico o mensaje de no encontrado.
        - source_links (list): URLs de los resultados usados.
        - error (str, opcional): descripción del error.
    """
    query = args.get('query')
    api_key = args.get('api_key')
    if not query or not api_key:
        return {"ok": False, "error": "Faltan 'query' o 'api_key'"}

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "hl": "es",  # results in Spanish when possible
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            return {"ok": False, "error": f"Código HTTP {resp.status_code}"}
        data = resp.json()
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Error de red: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"Respuesta no es JSON: {str(e)}"}

    organic = data.get('organic_results', [])
    if not organic:
        return {"ok": True, "summary": "información no encontrada", "source_links": []}

    # Palabras clave que indican contenido biográfico/profesional
    keywords = [
        "ocupación", "trabaja", "trabaja como", "profesional", "perfil", "estudios",
        "estudiante", "ingeniero", "doctor", "licenciado", "universidad",
        "empresa", "fundador", "cofundador", "investigador", "músico", "artista",
        "director", "gerente", "candidatura", "carrera", "experiencia", "biografía",
        "bio", "cv", "currículum"
    ]

    snippets = []
    source_links = []
    for entry in organic:
        title = entry.get('title', '')
        snippet = entry.get('snippet', '')
        link = entry.get('link')
        # combinar title y snippet para búsqueda de keywords
        text = f"{title} {snippet}".lower()
        if any(kw in text for kw in keywords):
            # limpiar texto simple
            clean = snippet.strip()
            if clean and clean not in snippets:
                snippets.append(clean)
                if link:
                    source_links.append(link)

    if not snippets:
        # fallback: si no se encuentran keywords, tratamos de usar los primeros 2 snippets genéricos
        fallback = []
        for entry in organic[:2]:
            snippet = entry.get('snippet', '').strip()
            if snippet:
                fallback.append(snippet)
                if entry.get('link'):
                    source_links.append(entry['link'])
        if fallback:
            summary = " ".join(fallback)
            return {"ok": True, "summary": summary, "source_links": source_links}
        else:
            return {"ok": True, "summary": "información no encontrada", "source_links": []}

    # Eliminar repeticiones parciales y unir en un párrafo
    # Simplemente unir fragmentos con espacio y capitalizar primera letra
    combined = " ".join(snippets)
    # Normalizar espacios y capitalizar
    combined = ' '.join(combined.split())
    if combined:
        combined = combined[0].upper() + combined[1:]
    else:
        combined = "información no encontrada"

    return {"ok": True, "summary": combined, "source_links": source_links}
