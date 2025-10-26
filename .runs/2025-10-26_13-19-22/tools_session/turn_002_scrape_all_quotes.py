import requests
import json
import os
import time
from bs4 import BeautifulSoup
from typing import Dict, List


def _extract_quotes_from_html(html: str) -> List[Dict[str, object]]:
    """Extrae citas, autor y etiquetas de una página HTML de quotes.toscrape.com."""
    soup = BeautifulSoup(html, "html.parser")
    quotes_data = []
    for quote in soup.select("div.quote"):
        text = quote.select_one("span.text").get_text(strip=True)
        author = quote.select_one("small.author").get_text(strip=True)
        tags = [tag.get_text(strip=True) for tag in quote.select("div.tags a.tag")]
        quotes_data.append({"text": text, "author": author, "tags": tags})
    return quotes_data


def _run_unit_tests() -> Dict[str, object]:
    """Ejecuta pruebas unitarias simples para validar la extracción de una página simulada."""
    sample_html = """
    <html><head></head><body>
      <div class="quote">
        <span class="text">\"Life is what happens when you’re busy making other plans.\"</span>
        <small class="author">John Lennon</small>
        <div class="tags">
          <a class="tag" href="/tag/life/page/1/">life</a>
          <a class="tag" href="/tag/plans/page/1/">plans</a>
        </div>
      </div>
    </body></html>
    """
    expected = [{
        "text": "\"Life is what happens when you’re busy making other plans.\"",
        "author": "John Lennon",
        "tags": ["life", "plans"]
    }]
    try:
        result = _extract_quotes_from_html(sample_html)
        assert result == expected, f"Extracción incorrecta. Esperado {expected}, obtenido {result}"
        return {"ok": True, "message": "Todas las pruebas unitarias pasaron"}
    except AssertionError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": f"Error inesperado en pruebas: {e}"}


def scrape_all_quotes(args: dict) -> dict:
    """Recorre todas las páginas de quotes.toscrape.com, extrae citas y las guarda en 'quotes.json'.
    Devuelve información resumida y resultados de pruebas unitarias.
    """
    base_url = "https://quotes.toscrape.com"
    next_page = "/"
    all_quotes: List[Dict[str, object]] = []
    page_number = 0
    max_retries = 3
    timeout_seconds = 10

    while next_page:
        page_number += 1
        url = base_url + next_page
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, timeout=timeout_seconds)
                if response.status_code != 200:
                    return {
                        "ok": False,
                        "error": f"Error HTTP {response.status_code} al solicitar {url}. Abortando."
                    }
                html = response.text
                break  # salida del bucle de reintentos si todo va bien
            except requests.exceptions.RequestException as e:
                if attempt == max_retries:
                    return {
                        "ok": False,
                        "error": f"Fallo de red después de {max_retries} intentos al solicitar {url}: {e}"
                    }
                # espera antes de reintentar
                time.sleep(2 ** attempt)
        # extracción de citas de la página actual
        page_quotes = _extract_quotes_from_html(html)
        # validación de 10 citas por página (excepto la última que puede tener menos)
        if len(page_quotes) != 10 and "next" in html.lower():
            return {
                "ok": False,
                "error": f"Se esperaban 10 citas en la página {page_number}, pero se obtuvieron {len(page_quotes)}."
            }
        all_quotes.extend(page_quotes)
        # buscar enlace a la siguiente página
        soup = BeautifulSoup(html, "html.parser")
        next_link = soup.select_one("li.next a")
        next_page = next_link["href"] if next_link else None

    # Guardar resultados en JSON
    output_path = os.path.join(os.getcwd(), "quotes.json")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_quotes, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return {"ok": False, "error": f"Error al escribir el archivo JSON: {e}"}

    # Ejecutar pruebas unitarias
    test_results = _run_unit_tests()

    return {
        "ok": True,
        "total_pages": page_number,
        "total_quotes": len(all_quotes),
        "file_path": output_path,
        "unit_tests": test_results
    }
