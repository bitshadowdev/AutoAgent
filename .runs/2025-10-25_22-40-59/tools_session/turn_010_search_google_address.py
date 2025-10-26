import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

def search_google_address(args: dict) -> dict:
    query = args.get('query', '')
    max_results = int(args.get('max_results', 5))
    if not query:
        return {'ok': False, 'error': 'Missing query parameter'}
    # Construir URL de búsqueda
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
    # Opciones de Chrome
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Evitar detección de automatización
    options.add_argument('--disable-blink-features=AutomationControlled')
    # Crear driver
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        return {'ok': False, 'error': f'Error al iniciar WebDriver: {e}'}
    try:
        driver.set_page_load_timeout(30)
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        # Gestionar posible popup de consentimiento de cookies
        try:
            consent_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'acepto') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i agree') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]")
            )
            consent_btn.click()
        except (TimeoutException, NoSuchElementException):
            pass  # No aparece el popup
        # Esperar a que los resultados estén presentes
        results_elements = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g'))
        )
        results = []
        for elem in results_elements:
            if len(results) >= max_results:
                break
            try:
                title_elem = elem.find_element(By.TAG_NAME, 'h3')
                link_elem = elem.find_element(By.TAG_NAME, 'a')
                title = title_elem.text.strip()
                link = link_elem.get_attribute('href')
                if title and link:
                    results.append({'title': title, 'url': link})
            except NoSuchElementException:
                continue
        return {'ok': True, 'results': results}
    except TimeoutException as e:
        # Capturar HTML para depuración
        html = ''
        try:
            html = driver.page_source
        except Exception:
            pass
        return {'ok': False, 'error': f'Timeout waiting for elements: {e}', 'page_source': html[:1000]}
    except WebDriverException as e:
        return {'ok': False, 'error': f'WebDriver exception: {e}'}
    finally:
        try:
            driver.quit()
        except Exception:
            pass