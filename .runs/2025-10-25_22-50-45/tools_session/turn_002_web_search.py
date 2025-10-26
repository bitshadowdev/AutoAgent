import requests
import json

def web_search(args: dict) -> dict:
    """Buscar información en la web usando la API pública de DuckDuckGo.

    Parámetros esperados (en *args*):
        - query (str): término de búsqueda a consultar. **Obligatorio** y no vacío.
    
    Retorna un dict JSON‑serializable con una de las siguientes estructuras:
        {'ok': True, 'results': [...]}   # lista de resultados relevantes
        {'ok': False, 'error': 'mensaje descriptivo'}
    """
    try:
        # Validar que la clave 'query' exista y no esté vacía
        query = args.get('query')
        if not isinstance(query, str) or not query.strip():
            return {'ok': False, 'error': 'El parámetro "query" es obligatorio y no puede estar vacío.'}
        query = query.strip()

        # Construir la URL de la API de DuckDuckGo (formato JSON)
        url = 'https://api.duckduckgo.com/'
        params = {
            'q': query,
            'format': 'json',
            'no_html': 1,
            'skip_disambig': 1
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return {'ok': False, 'error': f'Error HTTP {resp.status_code} al consultar la API.'}

        data = resp.json()
        # DuckDuckGo devuelve un campo 'AbstractText' y una lista de 'RelatedTopics'
        results = []
        abstract = data.get('AbstractText')
        if abstract:
            results.append({'type': 'abstract', 'text': abstract, 'url': data.get('AbstractURL')})
        # Extraer algunos temas relacionados (máximo 5)
        for topic in data.get('RelatedTopics', [])[:5]:
            if isinstance(topic, dict):
                if 'Text' in topic and 'FirstURL' in topic:
                    results.append({'type': 'related', 'text': topic['Text'], 'url': topic['FirstURL']})
        if not results:
            return {'ok': False, 'error': 'No se encontraron resultados para la consulta.'}
        return {'ok': True, 'results': results}
    except requests.RequestException as e:
        return {'ok': False, 'error': f'Error de conexión: {str(e)}'}
    except Exception as e:
        return {'ok': False, 'error': f'Excepción inesperada: {str(e)}'}

# ---------------------------------------------------------------------------
# Pruebas unitarias (usando la librería estándar unittest). Estas pruebas no
# se ejecutan automáticamente aquí, pero sirven como referencia para validar
# el comportamiento de la herramienta.
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import unittest

    class TestWebSearch(unittest.TestCase):
        def test_missing_query(self):
            self.assertEqual(
                web_search({}),
                {'ok': False, 'error': 'El parámetro "query" es obligatorio y no puede estar vacío.'}
            )

        def test_empty_query(self):
            self.assertEqual(
                web_search({'query': '   '}),
                {'ok': False, 'error': 'El parámetro "query" es obligatorio y no puede estar vacío.'}
            )

        def test_valid_query(self):
            result = web_search({'query': 'Python programming'})
            self.assertTrue(result.get('ok'))
            self.assertIn('results', result)
            self.assertIsInstance(result['results'], list)

    unittest.main()
