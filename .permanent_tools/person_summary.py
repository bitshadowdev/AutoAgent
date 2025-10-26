import requests
import json
import re

def person_summary(args: dict) -> dict:
    """Obtiene y sintetiza información biográfica de una persona mediante SerpAPI.
    Args:
        args: {
            'query': str,        # nombre a buscar
            'api_key': str       # clave de SerpAPI
        }
    Returns:
        dict con claves:
            - ok (bool): True si la operación tuvo éxito.
            - summary (str): párrafo biográfico o mensaje de información no encontrada.
            - source_links (list): URLs de los resultados usados.
            - error (str, opcional): mensaje de error en caso de fallo.
    """
    query = args.get('query')
    api_key = args.get('api_key')
    if not query or not api_key:
        return {'ok': False, 'error': 'Faltan "query" o "api_key" en los argumentos.'}

    url = 'https://serpapi.com/search.json'
    params = {
        'engine': 'google',
        'q': query,
        'api_key': api_key,
        'hl': 'es',            # resultados en español cuando sea posible
        'num': '20'
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Código HTTP inesperado: {response.status_code}'}
        data = response.json()
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error de red: {str(e)}'}
    except json.JSONDecodeError as e:
        return {'ok': False, 'error': f'Error al parsear JSON: {str(e)}'}

    # extraer resultados orgánicos
    organic = data.get('organic_results', [])
    if not organic:
        return {'ok': False, 'error': 'No se obtuvieron resultados orgánicos del motor de búsqueda.'}

    # palabras clave para considerar un snippet como biográfico/profesional
    keywords = [
        'ocupación', 'profesión', 'trabaja', 'trabaja en', 'estudia', 'estudio', 'graduado',
        'ingeniero', 'ingeniera', 'doctor', 'doctora', 'universidad', 'empresa', 'compañía',
        'perfil', 'biografía', 'bio', 'linkedin', 'kaggle', 'pinterest', 'autor', 'músico',
        'director', 'fundador', 'cofundador', 'investigador', 'estudiante', 'profesor',
        'educación', 'formación', 'reside', 'vive en', 'habita', 'ciudad', 'santiago', 'chil'
    ]

    def is_relevant(snippet: str) -> bool:
        snippet_low = snippet.lower()
        return any(kw in snippet_low for kw in keywords)

    relevant_snippets = []
    source_links = []
    for item in organic:
        title = item.get('title', '')
        snippet = item.get('snippet') or item.get('rich_snippet', {}).get('top', {}).get('detected_entities', '')
        link = item.get('link')
        if not snippet:
            continue
        if is_relevant(snippet):
            # limpiar texto
            clean = re.sub(r'\s+', ' ', snippet).strip()
            relevant_snippets.append(clean)
            if link:
                source_links.append(link)
        else:
            # también consideramos el título si contiene la palabra clave
            if is_relevant(title):
                clean = re.sub(r'\s+', ' ', title).strip()
                relevant_snippets.append(clean)
                if link:
                    source_links.append(link)

    if not relevant_snippets:
        return {
            'ok': True,
            'summary': 'información no encontrada',
            'source_links': source_links,
            'note': 'Se sugiere consultar directamente perfiles en LinkedIn, Kaggle o redes sociales.'
        }

    # eliminar duplicados conservando orden
    seen = set()
    uniq_snippets = []
    for s in relevant_snippets:
        if s not in seen:
            seen.add(s)
            uniq_snippets.append(s)

    # combinar en un párrafo único
    paragraph = ' '.join(uniq_snippets)
    # intentar recortar a una longitud razonable (≈ 500 chars)
    if len(paragraph) > 600:
        paragraph = paragraph[:597] + '...'

    return {
        'ok': True,
        'summary': paragraph,
        'source_links': list(dict.fromkeys(source_links))  # eliminar duplicados manteniendo orden
    }
