import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

def search_google_address(args: dict) -> dict:
    query = args.get('query', '')
    max_results = int(args.get('max_results', 5))
    results = []
    driver = None
    try:
        # Configuración del driver Chrome en modo headless
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # Inicializar driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(30)
        wait = WebDriverWait(driver, 15)

        # Ir a Google
        driver.get('https://www.google.com')
        # Aceptar cookies si aparece el banner (Google suele mostrarlo en algunos países)
        try:
            consent_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Acepta todo')] | //div[contains(@aria-label, 'Aceptar')]")))
            consent_btn.click()
        except Exception:
            pass  # Si no aparece, continuar

        # Localizar la barra de búsqueda, introducir la query y enviar
        search_box = wait.until(EC.presence_of_element_located((By.NAME, 'q')))
        search_box.clear()
        search_box.send_keys(query)
        search_box.submit()

        # Esperar a que los resultados se carguen
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g')))
        # Obtener los contenedores de resultados
        result_elements = driver.find_elements(By.CSS_SELECTOR, 'div.g')
        for elem in result_elements:
            if len(results) >= max_results:
                break
            try:
                title_elem = elem.find_element(By.TAG_NAME, 'h3')
                link_elem = elem.find_element(By.TAG_NAME, 'a')
                title = title_elem.text.strip()
                url = link_elem.get_attribute('href')
                if title and url:
                    results.append({'title': title, 'url': url})
            except NoSuchElementException:
                continue
        return {'ok': True, 'results': results}
    except (TimeoutException, WebDriverException) as e:
        return {'ok': False, 'error': f'Selenium error: {str(e)}'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass