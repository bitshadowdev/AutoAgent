import requests
import json
import re

def get_person_summary(args: dict) -> dict:
    """Consulta SerpAPI, filtra información biográfica y devuelve un resumen.
    Args:
        args: dict con claves:
            - query (str): término de búsqueda.
            - api_key (str): clave de SerpAPI.
    Returns:
        dict con:
            - ok (bool): True si se obtuvo información.
            - summary (str): párrafo resumido o mensaje de no encontrado.
            - source_links (list): URLs de los resultados relevantes.
    """
    query = args.get('query')
    api_key = args.get('api_key')
    if not query or not api_key:
        return {"ok": False, "error": "Faltan parámetros query o api_key"}
    try:
        url = 'https://serpapi.com/search.json'
        params = {
            'engine': 'google',
            'q': query,
            'hl': 'es',
            'api_key': api_key,
            'num': '10'
        }
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            return {"ok": False, "error": f"Código HTTP {resp.status_code}"}
        data = resp.json()
        organic = data.get('organic_results', [])
        # Filtrar snippets que contengan palabras clave biográficas
        keywords = [
            'ocupaci', 'estudios', 'trabaja', 'profesional', 'perfil',
            'universidad', 'empresa', 'cargo', 'licenci', 'doctor',
            'ingenier', 'estudiante', 'colegio', 'institut', 'fundador',
            'colaborador', 'afili', 'ubicaci', 'reside', 'nacido', 'nacimiento'
        ]
        relevant = []
        links = []
        for item in organic:
            snippet = item.get('snippet') or item.get('title') or ''
            lower = snippet.lower()
            if any(k in lower for k in keywords):
                # limpiar HTML y caracteres extra
                clean = re.sub(r'<[^>]+>', '', snippet)
                clean = re.sub(r'\s+', ' ', clean).strip()
                if clean:
                    relevant.append(clean)
                    link = item.get('link')
                    if link:
                        links.append(link)
        if not relevant:
            return {"ok": False, "summary": "información no encontrada", "source_links": []}
        # Eliminar redundancias simples
        unique = []
        for txt in relevant:
            if txt not in unique:
                unique.append(txt)
        # Construir párrafo
        summary = ' '.join(unique)
        # Truncar a 500 chars para evitar exceso
        summary = summary[:500].strip()
        return {"ok": True, "summary": summary, "source_links": list(dict.fromkeys(links))}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Error de red: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"Excepción inesperada: {str(e)}"}