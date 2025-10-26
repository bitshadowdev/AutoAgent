import requests
import re

def get_casona_nueva_address(args: dict) -> dict:
    """Obtiene la dirección de la Casona Nueva (Santiago, Chile).
    Primero consulta la Wikipedia en español mediante su API; si no encuentra
    la dirección, realiza una búsqueda en DuckDuckGo y extrae la primera coincidencia.
    Devuelve {'ok': True, 'address': '...'} o {'ok': False, 'error': '...'}.
    """
    try:
        # 1. Buscar página en Wikipedia en español
        search_url = (
            "https://es.wikipedia.org/w/api.php"
            "?action=opensearch&search=Casona%20Nueva%20Santiago%20Chile&limit=1&namespace=0&format=json"
        )
        resp = requests.get(search_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if len(data) >= 4 and data[3]:
            page_url = data[3][0]
        else:
            page_url = None

        address = None
        if page_url:
            # 2. Obtener contenido wikitexto de la página
            title_match = re.search(r"/wiki/(.+)$", page_url)
            if title_match:
                title = title_match.group(1)
                api_url = (
                    "https://es.wikipedia.org/w/api.php"
                    "?action=query&prop=revisions&rvprop=content&format=json&titles=" + title
                )
                page_resp = requests.get(api_url, timeout=10)
                page_resp.raise_for_status()
                page_data = page_resp.json()
                pages = page_data.get('query', {}).get('pages', {})
                for page in pages.values():
                    wikitext = page.get('revisions', [{}])[0].get('*', '')
                    # Buscar la línea de la infobox que contenga "Dirección" o "Dirección:"
                    match = re.search(r"\|\s*Dirección\s*=\s*([^\n\|]+)", wikitext, re.IGNORECASE)
                    if match:
                        address = match.group(1).strip()
                        break
        # 3. Si no se halló en Wikipedia, fallback a DuckDuckGo
        if not address:
            duck_url = "https://duckduckgo.com/html/"
            params = {"q": "Casona Nueva Santiago Chile dirección"}
            duck_resp = requests.post(duck_url, data=params, timeout=10)
            duck_resp.raise_for_status()
            # Buscar fragmentos que parezcan direcciones chilenas (ej. "Av. ...")
            snippets = re.findall(r"<a[^>]*class='result__a'[^>]*>(.*?)</a>", duck_resp.text, re.DOTALL)
            for snippet in snippets:
                # Limpiar HTML tags
                text = re.sub(r"<[^>]+>", "", snippet)
                # heurística simple: buscar número seguido de "Av" o "Calle"
                addr_match = re.search(r"\d+\s+(Av\.?|Avenida|Calle)\s+[A-Za-záéíóúñÑ]+", text, re.IGNORECASE)
                if addr_match:
                    address = addr_match.group(0)
                    break
        if address:
            return {"ok": True, "address": address}
        else:
            return {"ok": False, "error": "No se encontró la dirección en Wikipedia ni en DuckDuckGo."}
    except requests.RequestException as e:
        return {"ok": False, "error": f"Error de red: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": f"Error inesperado: {str(e)}"}