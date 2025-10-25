def get_quotes(args):
    import json, sys, subprocess, os, time
    # Instalar dependencias si es necesario
    try:
        import selenium
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', 'selenium', 'webdriver-manager'])
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    # Configurar Chrome en modo headless
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Crear driver
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    try:
        driver.get('https://quotes.toscrape.com/')
        time.sleep(2)  # esperar a que cargue
        quote_elements = driver.find_elements(By.CLASS_NAME, 'quote')
        quotes = []
        for el in quote_elements:
            text_el = el.find_element(By.CLASS_NAME, 'text')
            author_el = el.find_element(By.CLASS_NAME, 'author')
            quotes.append({
                'texto': text_el.text.strip('“”'),
                'autor': author_el.text
            })
        return {'quotes': quotes}
    finally:
        driver.quit()
