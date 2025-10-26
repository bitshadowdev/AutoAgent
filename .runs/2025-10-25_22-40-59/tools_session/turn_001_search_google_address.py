import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def search_google_address(args: dict) -> dict:
    """Busca en Google la query especificada y devuelve los primeros resultados.
    Args:
        args: dict con la clave 'query' (texto a buscar) y opcional 'max_results' (int, default 5).
    Returns:
        dict con 'ok', 'results' (lista de dict con 'title' y 'url') o 'error'.
    """
    query = args.get('query', '')
    max_results = int(args.get('max_results', 5))
    if not query:
        return {'ok': False, 'error': 'Se debe proporcionar una consulta en "query".'}
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        driver.get('https://www.google.com')
        # Aceptar cookies si aparece (Google ES)
        try:
            consent_button = driver.find_element(By.XPATH, "//button[contains(., 'Acepto')]")
            consent_button.click()
        except Exception:
            pass
        search_box = driver.find_element(By.NAME, 'q')
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        # Esperar a que aparezcan resultados
        driver.implicitly_wait(5)
        result_elements = driver.find_elements(By.XPATH, "//div[@class='g']//div[@class='yuRUbf']/a")[:max_results]
        results = []
        for elem in result_elements:
            title_elem = elem.find_element(By.TAG_NAME, 'h3')
            title = title_elem.text if title_elem else ''
            url = elem.get_attribute('href')
            results.append({'title': title, 'url': url})
        driver.quit()
        return {'ok': True, 'results': results}
    except Exception as e:
        return {'ok': False, 'error': str(e)}