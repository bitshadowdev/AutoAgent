import requests
import re
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

def get_casona_nueva_address(args: dict) -> dict:
    """Obtiene la dirección de la Casona Nueva (Santiago, Chile).
    Retorna {'ok': True, 'address': '<dirección>'} o {'ok': False, 'error': '<mensaje>'}.
    """
    query = "Casona Nueva Santiago Chile"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Bot/0.1)"}

    # ---------- Wikipedia ----------
    try:
        wp_search_url = (
            "https://es.wikipedia.org/w/api.php"
            "?action=opensearch&search=" + requests.utils.quote(query) +
            "&limit=1&namespace=0&format=json"
        )
        resp = requests.get(wp_search_url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if len(data) >= 4 and data[3]:
            page_url = data[3][0]
            # Obtener contenido HTML de la página
            wp_parse_url = (
                "https://es.wikipedia.org/w/api.php"
                "?action=parse&page=" + requests.utils.quote(data[1][0]) +
                "&prop=text&formatversion=2&format=json"
            )
            resp2 = requests.get(wp_parse_url, headers=headers, timeout=10)
            resp2.raise_for_status()
            page_data = resp2.json()
            html = page_data.get('parse', {}).get('text', '')
            soup = BeautifulSoup(html, "html.parser")
            # buscar tabla infobox
            infobox = soup.find('table', {'class': re.compile('infobox')})
            if infobox:
                # buscar fila que contenga la palabra "Dirección" o "Ubicación"
                for tr in infobox.find_all('tr'):
                    th = tr.find('th')
                    if th and re.search(r'Direcci[oó]n|Ubicaci[oó]n', th.get_text(), re.IGNORECASE):
                        td = tr.find('td')
                        if td:
                            address = td.get_text(separator=' ', strip=True)
                            return {'ok': True, 'address': address}
    except RequestException as e:
        return {'ok': False, 'error': f"Error de red Wikipedia: {e}"}
    except Exception as e:
        # Continuar al fallback si ocurre algún error inesperado
        pass

    # ---------- DuckDuckGo ----------
    try:
        ddg_url = "https://duckduckgo.com/html/"
        params = {"q": query}
        resp = requests.post(ddg_url, data=params, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = soup.select('.result__body')
        for res in results:
            snippet = res.get_text(separator=' ', strip=True)
            # buscar patrón típico de dirección chilena
            match = re.search(r"\b\d{1,5}\s+([A-Za-záéíóúñÁÉÍÓÚÑ]+\s?)+,\s*Santiago\s*[-–]?\s*Chile\b", snippet, re.IGNORECASE)
            if match:
                return {'ok': True, 'address': match.group(0)}
        # Si no se encontró con patrón, intentar devolver el primer resultado completo
        if results:
            first = results[0].get_text(separator=' ', strip=True)
            return {'ok': True, 'address': first}
    except RequestException as e:
        return {'ok': False, 'error': f"Error de red DuckDuckGo: {e}"}
    except Exception as e:
        return {'ok': False, 'error': f"Error inesperado DuckDuckGo: {e}"}

    return {'ok': False, 'error': 'No se encontró dirección en Wikipedia ni en DuckDuckGo.'}
