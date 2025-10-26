import sys
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote_plus

def search_google_address(args: dict) -> dict:
    """Busca *args['query']* en Google y devuelve hasta *args['max_results']* resultados.
    Cada resultado es un dict con 'title' y 'url'.
    """
    query = args.get('query', '')
    max_results = int(args.get('max_results', 5))
    if not query:
        return {'ok': False, 'error': 'query parameter is required'}
    try:
        # Chrome options
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # Create driver
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        wait = WebDriverWait(driver, 15)
        # Build search URL
        search_url = f"https://www.google.com/search?q={quote_plus(query)}"
        driver.get(search_url)
        # Handle possible consent popup (Google's "I agree" button)
        try:
            consent_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//div[contains(text(),'I agree')]] | //button[contains(text(),'Acepto')]| //div[contains(text(),'I agree')]/parent::button"))
            )
            consent_btn.click()
            # After clicking consent, wait a short moment for results to load again
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g')))
        except (TimeoutException, NoSuchElementException):
            # No consent popup detected; continue
            pass
        # Wait for search results container
        results_elements = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g'))
        )
        results = []
        for elem in results_elements:
            if len(results) >= max_results:
                break
            try:
                # Google may have different structures; try to get h3 and a
                h3 = elem.find_element(By.TAG_NAME, 'h3')
                a = elem.find_element(By.TAG_NAME, 'a')
                title = h3.text.strip()
                url = a.get_attribute('href')
                if title and url:
                    results.append({'title': title, 'url': url})
            except NoSuchElementException:
                continue
        return {'ok': True, 'results': results}
    except Exception as e:
        tb = traceback.format_exc()
        return {'ok': False, 'error': str(e), 'trace': tb}
    finally:
        try:
            driver.quit()
        except Exception:
            pass
