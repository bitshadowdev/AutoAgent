import requests
import re

def get_person_summary(args: dict) -> dict:
    """Consulta SerpAPI y genera un resumen biográfico para una persona.
    Args:
        args: {
            "query": "nombre a buscar",
            "api_key": "clave de SerpAPI"
        }
    Returns:
        dict con 'ok', 'summary', 'source_links' y opcionalmente 'error'.
    """
    query = args.get('query')
    api_key = args.get('api_key')
    if not query or not api_key:
        return {"ok": False, "error": "Faltan parámetros 'query' o 'api_key'"}
    try:
        url = 'https://serpapi.com/search.json'
        params = {
            'engine': 'google',
            'q': query,
            'api_key': api_key,
            'num': 10,
        }
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            return {"ok": False, "error": f"HTTP {resp.status_code}"}
        data = resp.json()
        organic = data.get('organic_results', [])
        # Filtrar resultados que parezcan biográficos o profesionales
        bio_snippets = []
        source_links = []
        for item in organic:
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            link = item.get('link', '')
            # Heurística simple para identificar contenido biográfico
            if re.search(r"(?i)\b(profile|linkedin|bio|biography|curriculum|resume|occupation|position|title|company|university|study|certified|team|member)\b", snippet) \
               or re.search(r"(?i)\b(profile|linkedin|bio|biography|curriculum|resume|occupation|position|title|company|university|study|certified|team|member)\b", title):
                clean = re.sub(r"\s+", " ", snippet).strip()
                if clean:
                    bio_snippets.append(clean)
                    if link:
                        source_links.append(link)
        # Si no encontramos nada, usar los primeros snippets como fallback (baja confianza)
        if not bio_snippets:
            for item in organic[:5]:
                snippet = item.get('snippet', '')
                if snippet:
                    bio_snippets.append(re.sub(r"\s+", " ", snippet).strip())
                    link = item.get('link')
                    if link:
                        source_links.append(link)
        # Síntesis: eliminar duplicados y combinar en un párrafo
        seen = set()
        unique_sentences = []
        for txt in bio_snippets:
            parts = re.split(r"(?<=[.!?])\s+", txt)
            for p in parts:
                p = p.strip()
                if p and p not in seen:
                    seen.add(p)
                    unique_sentences.append(p)
        summary = " ".join(unique_sentences)
        if not summary:
            return {"ok": False, "error": "Información no encontrada"}
        # Eliminar enlaces duplicados manteniendo el orden
        source_links = list(dict.fromkeys(source_links))
        return {"ok": True, "summary": summary, "source_links": source_links}
    except Exception as e:
        return {"ok": False, "error": str(e)}