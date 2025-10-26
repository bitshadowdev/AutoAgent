import json
import time
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def search_google_address(args: dict) -> dict:
    """Busca la consulta en Google y devuelve los primeros resultados.
    args:
        query (str): texto de búsqueda.
        max_results (int): número máximo de resultados a devolver.
    Returns:
        dict con {'ok': bool, 'results': [...]} o {'ok': False, 'error': str}
    """
    query = args.get('query', '')
    max_results = int(args.get('max_results', 5))
    if not query:
        return {'ok': False, 'error': 'query parameter is required'}
    # Configuración del driver
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    except Exception as e:
        return {'ok': False, 'error': f'Failed to start Chrome driver: {e}'}
    results = []
    try:
        # Construir URL de búsqueda directa
        encoded = quote_plus(query)
        url = f'https://www.google.com/search?q={encoded}'
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        # Gestionar posible popup de consentimiento de cookies
        try:
            consent_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'acepto') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'i agree') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept all')]))
            consent_btn.click()
        except (TimeoutException, NoSuchElementException):
            pass  # No hay popup
        # Esperar a que aparezcan los resultados
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g')))
        result_elements = driver.find_elements(By.CSS_SELECTOR, 'div.g')
        for elem in result_elements:
            try:
                title_elem = elem.find_element(By.TAG_NAME, 'h3')
                link_elem = elem.find_element(By.TAG_NAME, 'a')
                title = title_elem.text
                link = link_elem.get_attribute('href')
                if title and link:
                    results.append({'title': title, 'url': link})
                if len(results) >= max_results:
                    break
            except NoSuchElementException:
                continue
        return {'ok': True, 'results': results}
    except TimeoutException as te:
        return {'ok': False, 'error': f'Timeout waiting for elements: {te}'}
    except WebDriverException as we:
        return {'ok': False, 'error': f'WebDriver exception: {we}'}
    except Exception as e:
        return {'ok': False, 'error': f'Unexpected error: {e}'}
    finally:
        try:
            driver.quit()
        except Exception:
            pass