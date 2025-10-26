import requests
import json
import re
import unittest

def person_bio_tool(args: dict) -> dict:
    """Obtiene una biografía resumida de una persona usando SerpAPI.

    Parámetros:
        args (dict): {
            'query': str,       # nombre a buscar
            'api_key': str      # clave de SerpAPI
        }
    Retorno:
        dict con claves:
            - ok (bool): indica éxito.
            - summary (str): biografía sintetizada o mensaje de 'información no encontrada'.
            - source_links (list): URLs de los resultados usados.
            - error (str, opcional): descripción del error si ok es False.
    """
    query = args.get('query')
    api_key = args.get('api_key')
    if not query or not api_key:
        return {'ok': False, 'error': 'query y api_key son obligatorios'}
    try:
        # 1. petición a SerpAPI
        params = {'engine': 'google', 'q': query, 'api_key': api_key}
        response = requests.get('https://serpapi.com/search', params=params, timeout=10)
        if response.status_code != 200:
            return {'ok': False, 'error': f'HTTP {response.status_code}'}
        data = response.json()
        organic = data.get('organic_results', [])

        # 2. filtrado de snippets biográficos
        keywords = r"\b(ocupaci[oó]n|estudios|trabaja|profesional|instituci[oó]n|universidad|empresa|cargo|perfil|licenci|grado)\b"
        snippets = []
        for entry in organic:
            snippet = entry.get('snippet', '')
            title = entry.get('title', '')
            if re.search(keywords, snippet, re.I):
                snippets.append(f"{title}. {snippet}")

        # 3. calidad: si no hay datos útiles
        if not snippets:
            return {'ok': False, 'summary': 'información no encontrada', 'source_links': []}

        # 4. eliminación de repeticiones simples
        uniq_snippets = []
        for s in snippets:
            if s not in uniq_snippets:
                uniq_snippets.append(s)
        combined = " ".join(uniq_snippets)

        # 5. síntesis (truncamiento y formateo básico)
        summary = combined.strip()
        # limitar longitud para ser legible
        if len(summary) > 500:
            summary = summary[:497] + "..."

        # 6. enlaces de origen
        source_links = [e.get('link') for e in organic if e.get('link')]
        return {'ok': True, 'summary': summary, 'source_links': source_links}
    except requests.exceptions.RequestException as exc:
        return {'ok': False, 'error': str(exc)}

# ---------------------------------------------------------------
# Pruebas unitarias (no se ejecutan automáticamente aquí, pero sirven como referencia)
class TestPersonBioTool(unittest.TestCase):
    def test_missing_params(self):
        self.assertFalse(person_bio_tool({})['ok'])

    def test_no_bio(self):
        # Simulamos respuesta sin snippets biográficos mediante monkeypatch (ejemplo conceptual)
        pass

# ---------------------------------------------------------------
# README (documentación de uso)
"""
README
======
## Uso de la herramienta ``person_bio_tool``
```python
from person_bio_tool import person_bio_tool
result = person_bio_tool({
    'query': 'Israel Exequiel Huentecura',
    'api_key': 'TU_API_KEY_AQUI'
})
print(result)
```
### Parámetros
- **query**: nombre completo o término a buscar.
- **api_key**: clave personal de SerpAPI.

### Salida
- ``ok``: ``True`` si se obtuvo información útil.
- ``summary``: biografía sintetizada o ``información no encontrada``.
- ``source_links``: lista de URLs usadas como fuentes.
- ``error``: mensaje en caso de falla.

### Notas
- La herramienta filtra únicamente snippets que contengan palabras clave relacionadas con ocupación, estudios o afiliaciones.
- Si no se hallan datos biográficos, se sugiere consultar directamente LinkedIn, Kaggle u otras fuentes.
"""
