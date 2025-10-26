import requests
import json
import re
from typing import Dict, List

def get_person_summary(args: dict) -> dict:
    """Obtiene un resumen biográfico de una persona usando la API de SerpAPI.

    Parámetros:
        args (dict): {
            'query': str,      # nombre a buscar
            'api_key': str     # clave de SerpAPI
        }
    
    Retorna:
        dict con los campos:
            - ok (bool): indica si la operación fue exitosa
            - summary (str): párrafo biográfico o mensaje de información no encontrada
            - source_links (list): URLs de los resultados utilizados
            - error (str, opcional): mensaje de error en caso de falla
    """
    # ------------------- Validación de argumentos -------------------
    query = args.get('query')
    api_key = args.get('api_key')
    if not query or not api_key:
        return {'ok': False, 'error': 'Faltan "query" o "api_key" en los argumentos.'}

    # ------------------- Petición a SerpAPI -------------------
    endpoint = 'https://serpapi.com/search.json'
    params = {
        'engine': 'google',
        'q': query,
        'api_key': api_key,
        'hl': 'es'  # resultados en español cuando sea posible
    }
    try:
        response = requests.get(endpoint, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return {'ok': False, 'error': f'Error de red o HTTP: {str(e)}'}
    except json.JSONDecodeError:
        return {'ok': False, 'error': 'Respuesta no es JSON válido.'}

    # ------------------- Extracción de resultados -------------------
    # SerpAPI puede devolver los resultados bajo distintas claves.
    results = data.get('organic_results') or data.get('results') or []
    if not isinstance(results, list):
        results = []

    # ------------------- Filtrado de información biográfica -------------------
    bio_keywords = [
        r'\bingenier\w*\b', r'estudiante', r'profesor', r'director',
        r'fundador', r'co[-\s]?founder', r'CEO', r'colega', r'universidad',
        r'empresa', r'compañ\w*', r'Chile', r'Santiago', r'colabor\w*',
        r'actividad', r'perfil', r'bio', r'biodata', r'curriculum', r'\btrabajo\b'
    ]
    bio_pattern = re.compile('|'.join(bio_keywords), re.IGNORECASE)

    filtered_snippets: List[str] = []
    source_links: List[str] = []
    for item in results:
        title = item.get('title', '')
        snippet = item.get('snippet', '') or item.get('snippet', '')
        link = item.get('link') or item.get('url')
        # Consideramos que el snippet contiene información útil si coincide con alguno de los patrones.
        if snippet and bio_pattern.search(snippet):
            cleaned = re.sub(r"\s+", " ", snippet).strip()
            filtered_snippets.append(cleaned)
            if link:
                source_links.append(link)
        elif title and bio_pattern.search(title):
            cleaned = re.sub(r"\s+", " ", title).strip()
            filtered_snippets.append(cleaned)
            if link:
                source_links.append(link)

    # ------------------- Síntesis del resumen -------------------
    if not filtered_snippets:
        # No se encontró información biográfica útil.
        suggestion = (
            "No se encontró información biográfica clara para Israel Exequiel Huentecura. "
            "Se recomienda consultar fuentes como LinkedIn, Kaggle o buscadores especializados."
        )
        return {
            'ok': True,
            'summary': suggestion,
            'source_links': source_links
        }

    # Eliminar repeticiones exactas y ordenar por relevancia (longitud descendente).
    unique_snippets = list(dict.fromkeys(filtered_snippets))
    unique_snippets.sort(key=lambda s: -len(s))
    # Concatenar en un solo párrafo, separando por espacios.
    summary = ' '.join(unique_snippets)
    # Limitar a 1000 caracteres para evitar respuestas excesivamente largas.
    summary = summary[:1000].rstrip()
    # Añadir punto final si falta.
    if not summary.endswith('.'):  # pragma: no cover
        summary += '.'

    return {
        'ok': True,
        'summary': summary,
        'source_links': list(dict.fromkeys(source_links))
    }
