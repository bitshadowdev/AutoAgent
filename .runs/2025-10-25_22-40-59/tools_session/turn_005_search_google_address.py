import json
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

def search_google_address(args: dict) -> dict:
    query = args.get('query')
    max_results = int(args.get('max_results', 5))
    results = []
    driver = None
    try:
        if not query:
            return {"ok": False, "error": "Missing 'query' parameter"}
        # Chrome options
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # Init driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        # Open Google
        driver.get('https://www.google.com')
        wait = WebDriverWait(driver, 15)
        # Accept cookies / consent if present
        try:
            consent_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.='I agree' or .='Accept all' or .='Acepto' or .='Aceptar todo']")))
            consent_btn.click()
        except Exception:
            pass  # No consent dialog
        # Locate search box, send query
        search_box = wait.until(EC.presence_of_element_located((By.NAME, 'q')))
        search_box.clear()
        search_box.send_keys(query)
        search_box.submit()
        # Wait for results container
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.g')))
        # Grab result elements
        elems = driver.find_elements(By.CSS_SELECTOR, 'div.g')
        for elem in elems:
            if len(results) >= max_results:
                break
            try:
                title_elem = elem.find_element(By.TAG_NAME, 'h3')
                link_elem = elem.find_element(By.TAG_NAME, 'a')
                title = title_elem.text.strip()
                url = link_elem.get_attribute('href')
                if title and url:
                    results.append({"title": title, "url": url})
            except NoSuchElementException:
                continue
        return {"ok": True, "results": results}
    except (TimeoutException, WebDriverException) as e:
        return {"ok": False, "error": f"Selenium error: {str(e)}", "trace": traceback.format_exc()}
    except Exception as e:
        return {"ok": False, "error": f"Unexpected error: {str(e)}", "trace": traceback.format_exc()}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass