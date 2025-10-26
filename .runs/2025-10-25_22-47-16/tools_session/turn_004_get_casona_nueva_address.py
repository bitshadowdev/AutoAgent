import requests
import re
from bs4 import BeautifulSoup

def get_casona_nueva_address(args: dict) -> dict:
    """Devuelve la dirección de la Casona Nueva (Santiago, Chile).
    Busca primero en Wikipedia (es.wikipedia.org) y, si no encuentra la información,
    realiza una búsqueda en DuckDuckGo y extrae la primera coincidencia que parezca una
    dirección física. Devuelve {'ok': True, 'address': '...'} o {'ok': False, 'error': '...'}.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; CasonaNuevaBot/1.0; +https://example.com/bot)'
    }
    query = 'Casona Nueva Santiago Chile'
    # ---------- Intento con Wikipedia ----------
    try:
        # 1) Obtener título exacto vía opensearch
        opensearch_url = ('https://es.wikipedia.org/w/api.php'
                          '?action=opensearch&search=' + requests.utils.quote(query) +
                          '&limit=1&namespace=0&format=json')
        resp = requests.get(opensearch_url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if len(data) >= 2 and data[1]:
            title = data[1][0]
            # 2) Obtener wikitexto de la página
            parse_url = ('https://es.wikipedia.org/w/api.php'
                         '?action=parse&prop=wikitext&page=' + requests.utils.quote(title) +
                         '&format=json')
            resp2 = requests.get(parse_url, headers=headers, timeout=10)
            resp2.raise_for_status()
            wikitext = resp2.json().get('parse', {}).get('wikitext', {}).get('*', '')
            # 3) Buscar plantilla de infobox que contenga "Dirección"
            match = re.search(r'Dirección\s*=\s*([^\n\|}]+)', wikitext, re.IGNORECASE)
            if match:
                address = match.group(1).strip()
                # Limpiar posibles referencias de archivo o etiquetas
                address = re.sub(r'\<[^>]*\>', '', address)
                address = re.sub(r'\[[^\]]*\]', '', address)
                return {'ok': True, 'address': address}
    except Exception as e:
        # Capturamos cualquier error de red o parsing y continuamos con fallback
        wiki_error = str(e)
    # ---------- Fallback con DuckDuckGo ----------
    try:
        ddg_url = 'https://duckduckgo.com/html/'
        params = {'q': query}
        resp = requests.post(ddg_url, data=params, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Los resultados aparecen en div.result
        for div in soup.select('div.result'):
            snippet = div.get_text(separator=' ', strip=True)
            # Intentamos extraer algo que parezca dirección chilena (número, calle, Santiago)
            addr_match = re.search(r'\d{1,4}\s+[^,]+\s+Santiago', snippet, re.IGNORECASE)
            if addr_match:
                address = addr_match.group(0).strip()
                return {'ok': True, 'address': address}
        # Si no se encontró en snippets, intentar analizar los enlaces
        for a in soup.select('a.result__a'):
            href = a.get('href', '')
            # Algunos enlaces pueden contener la dirección en la URL (poco probable)
        return {'ok': False, 'error': 'No se encontró dirección en DuckDuckGo.'}
    except Exception as e:
        ddg_error = str(e)
        # Si falló ambos, devolver error acumulado
        return {'ok': False, 'error': f'Falla en Wikipedia ({wiki_error if "wiki_error" in locals() else ""}) y DuckDuckGo ({ddg_error}).'}