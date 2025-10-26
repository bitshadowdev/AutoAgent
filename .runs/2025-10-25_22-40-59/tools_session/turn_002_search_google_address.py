import json
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

def search_google_address(args: dict) -> dict:
    """Busca una dirección en Google y devuelve los primeros resultados.

    Args:
        args: {
            'query': str,            # texto de búsqueda
            'max_results': int       # número máximo de resultados a devolver
        }
    Returns:
        dict con claves 'ok' (bool) y, si ok=True, 'results' (list de dict con 'title' y 'link'),
        o 'error' (str) si ocurre algún problema.
    """
    query = args.get('query', '')
    max_results = args.get('max_results', 5)
    if not query:
        return {'ok': False, 'error': 'El parámetro "query" es obligatorio.'}
    # Configurar Chrome headless
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        driver.get(search_url)
        # Esperar a que los resultados carguen
        driver.implicitly_wait(5)
        # Cada resultado típico está dentro de un div con clase 'g'
        result_elements = driver.find_elements(By.CSS_SELECTOR, 'div.g')
        results = []
        for elem in result_elements:
            if len(results) >= max_results:
                break
            try:
                # Título y enlace pueden variar; intentamos varias rutas
                title_elem = elem.find_element(By.TAG_NAME, 'h3')
                link_elem = elem.find_element(By.TAG_NAME, 'a')
                title = title_elem.text.strip()
                link = link_elem.get_attribute('href')
                if title and link:
                    results.append({'title': title, 'link': link})
            except Exception:
                # Si falla en un resultado, simplemente lo omitimos
                continue
        return {'ok': True, 'results': results}
    except WebDriverException as e:
        return {'ok': False, 'error': f'WebDriverException: {str(e)}'}
    except Exception as e:
        tb = traceback.format_exc()
        return {'ok': False, 'error': f'Unexpected error: {str(e)}', 'traceback': tb}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass