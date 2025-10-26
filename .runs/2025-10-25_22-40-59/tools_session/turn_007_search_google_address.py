import os
import sys
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

def search_google_address(args: dict) -> dict:
    """Busca una query en Google y devuelve los primeros resultados.

    Args:
        args: {
            'query': str,           # texto de búsqueda
            'max_results': int      # número máximo de resultados a devolver
        }
    Returns:
        dict con {'ok': True, 'results': [{'title':..., 'url':...}, ...]}
        o {'ok': False, 'error': <mensaje>}
    """
    query = args.get('query', '')
    max_results = int(args.get('max_results', 5))
    if not query:
        return {'ok': False, 'error': 'query no provisto'}

    # Configurar Chrome en modo headless
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    # Evitar que Chrome solicite permisos
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = None
    try:
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        # Construir URL de búsqueda directamente
        search_url = f"https://www.google.com/search?q={quote_plus(query)}"
        driver.get(search_url)

        # Manejar posible popup de consentimiento de cookies
        try:
            consent_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'acepto') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i agree')]")
            )
            consent_btn.click()
        except Exception:
            # No hay popup o no se pudo encontrar, continuar
            pass

        # Esperar a que los resultados estén presentes
        wait = WebDriverWait(driver, 15)
        result_elements = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g'))
        )

        results = []
        for elem in result_elements:
            if len(results) >= max_results:
                break
            try:
                # Título
                title_elem = elem.find_element(By.TAG_NAME, 'h3')
                title = title_elem.text.strip()
                # URL (el <a> que contiene el h3)
                link_elem = elem.find_element(By.TAG_NAME, 'a')
                url = link_elem.get_attribute('href')
                if title and url:
                    results.append({'title': title, 'url': url})
            except NoSuchElementException:
                continue
        return {'ok': True, 'results': results}
    except (TimeoutException, WebDriverException) as e:
        return {'ok': False, 'error': f'Selenium error: {str(e)}'}
    except Exception as e:
        return {'ok': False, 'error': f'Unexpected error: {str(e)}'}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
