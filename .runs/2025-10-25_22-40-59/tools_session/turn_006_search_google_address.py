import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

def search_google_address(args: dict) -> dict:
    """Busca en Google la query indicada y devuelve los primeros resultados.
    Args:
        args: {
            "query": "texto a buscar",
            "max_results": número máximo de resultados (opcional, por defecto 5)
        }
    Returns:
        dict con clave 'ok' y 'results' (lista de dicts con 'title' y 'url') o 'error'.
    """
    query = args.get('query')
    max_results = int(args.get('max_results', 5))
    if not query:
        return {'ok': False, 'error': 'Missing "query" parameter'}
    # Construir URL de búsqueda
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded_query}"

    # Opciones de Chrome
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    # Evitar detección de automatización
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(search_url)
        wait = WebDriverWait(driver, 15)
        # Manejar posible banner de consentimiento de cookies
        try:
            consent_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'ACEPTARACEPTAR','aceptaraceptar'), 'aceptar') or contains(translate(., 'I AGREE', 'i agree'), 'i agree') or contains(., 'I agree') or contains(., 'Acepto')]"))
            consent_btn.click()
            # Esperar que desaparezca el banner
            wait.until(EC.invisibility_of_element(consent_btn))
        except (TimeoutException, NoSuchElementException):
            # No hay banner de cookies
            pass
        # Esperar a que aparezcan los resultados
        results_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g')))
        results = []
        for elem in results_elements:
            if len(results) >= max_results:
                break
            try:
                # El título está en <h3>
                title_elem = elem.find_element(By.TAG_NAME, 'h3')
                title = title_elem.text.strip()
                # El enlace está en el <a> que envuelve al h3
                link_elem = elem.find_element(By.TAG_NAME, 'a')
                url = link_elem.get_attribute('href')
                if title and url:
                    results.append({'title': title, 'url': url})
            except (NoSuchElementException, Exception):
                continue
        return {'ok': True, 'results': results}
    except (TimeoutException, WebDriverException) as e:
        return {'ok': False, 'error': str(e)}
    except Exception as e:
        return {'ok': False, 'error': f'Unexpected error: {e}'}
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
