import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def search_google_address(args: dict) -> dict:
    query = args.get('query', '')
    max_results = int(args.get('max_results', 5))
    # Configurar Chrome en modo headless
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('window-size=1920,1080')
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)
        driver.get('https://www.google.com')
        # Manejar posible banner de consentimiento de cookies
        try:
            consent_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'acepto') or \
                                 contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i agree') or \
                                 contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]")
                )
            )
            consent_btn.click()
        except Exception:
            # Si no aparece el banner, continuar sin error
            pass
        # Buscar la query
        search_box = wait.until(EC.presence_of_element_located((By.NAME, 'q')))
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        # Esperar a que aparezcan los resultados
        results_container = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g')))
        results = []
        for elem in results_container:
            try:
                title_el = elem.find_element(By.TAG_NAME, 'h3')
                link_el = elem.find_element(By.TAG_NAME, 'a')
                title = title_el.text.strip()
                url = link_el.get_attribute('href')
                if title and url:
                    results.append({'title': title, 'url': url})
                if len(results) >= max_results:
                    break
            except Exception:
                continue
        return {'ok': True, 'results': results}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'trace': traceback.format_exc()}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass