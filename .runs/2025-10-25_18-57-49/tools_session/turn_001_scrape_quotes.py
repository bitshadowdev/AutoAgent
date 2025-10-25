def scrape_quotes(args):
    import json, os, sys, subprocess, base64, time
    # Instalar dependencias si es necesario
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
    except Exception:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', 'selenium', 'webdriver-manager'])
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
    url = args.get('url', 'http://quotes.toscrape.com')
    # Configurar Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.get(url)
    time.sleep(1)  # dar tiempo a carga
    quotes_elements = driver.find_elements(By.CSS_SELECTOR, "div.quote")
    results = []
    for el in quotes_elements:
        text = el.find_element(By.CSS_SELECTOR, "span.text").text.strip()
        author = el.find_element(By.CSS_SELECTOR, "small.author").text.strip()
        results.append({"text": text, "author": author})
    driver.quit()
    return {"quotes": results}
