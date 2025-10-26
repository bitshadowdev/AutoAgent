import requests
import time
import json
import os
from bs4 import BeautifulSoup
import unittest
from unittest.mock import patch, Mock

def scrape_all_quotes(args: dict) -> dict:
    """Scrapea todas las citas de https://quotes.toscrape.com y guarda un JSON.

    Parámetros en *args* (opcional):
        - run_tests (bool): si True, ejecuta pruebas unitarias y retorna su resultado.
    """
    try:
        # Si se solicitan pruebas, ejecutarlas y retornar el reporte
        if args.get('run_tests'):
            test_result = _run_tests()
            return {'ok': True, 'tests_passed': test_result.wasSuccessful(), 'tests_report': test_result}

        base_url = 'https://quotes.toscrape.com'
        next_url = '/'
        all_quotes = []
        session = requests.Session()
        max_retries = 3
        backoff_factor = 1

        while next_url:
            url = base_url + next_url
            for attempt in range(1, max_retries + 1):
                try:
                    response = session.get(url, timeout=10)
                    response.raise_for_status()
                    break  # éxito, salir del bucle de reintentos
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries:
                        return {'ok': False, 'error': f'Error de red al obtener {url}: {str(e)}'}
                    sleep_time = backoff_factor * (2 ** (attempt - 1))
                    time.sleep(sleep_time)
            soup = BeautifulSoup(response.text, 'html.parser')
            quote_elements = soup.select('div.quote')
            for q in quote_elements:
                text_el = q.select_one('span.text')
                author_el = q.select_one('small.author')
                if not text_el or not author_el:
                    continue  # saltar si falta alguno de los campos
                text = text_el.get_text(strip=True)
                author = author_el.get_text(strip=True)
                all_quotes.append({'text': text, 'author': author})
            # buscar link 'Next'
            next_btn = soup.select_one('li.next > a')
            next_url = next_btn['href'] if next_btn else None

        # Serializar a JSON
        json_str = json.dumps(all_quotes, ensure_ascii=False, indent=2)
        output_path = os.path.join(os.getcwd(), 'quotes.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
        return {'ok': True, 'file': output_path, 'count': len(all_quotes)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

# ---------------------------------------------------------------------------
# Funciones auxiliares para pruebas
def _run_tests():
    """Ejecuta el suite de pruebas unitarias definido abajo y devuelve el resultado."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(_ScrapeQuotesTestCase)
    runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'))  # silenciar salida
    result = runner.run(suite)
    return result

class _ScrapeQuotesTestCase(unittest.TestCase):
    def setUp(self):
        # HTML de la primera página simulada
        self.page1 = '''
        <html><body>
            <div class="quote"><span class="text">“Life is what happens when you're busy making other plans.”</span><small class="author">John Lennon</small></div>
            <div class="quote"><span class="text">“The greatest glory in living lies not in never falling, but in rising every time we fall.”</span><small class="author">Nelson Mandela</small></div>
            <li class="next"><a href="/page/2/">Next</a></li>
        </body></html>'''
        # HTML de la segunda página simulada (última)
        self.page2 = '''
        <html><body>
            <div class="quote"><span class="text">“To be yourself in a world that is constantly trying to make you something else is the greatest accomplishment.”</span><small class="author">Ralph Waldo Emerson</small></div>
            <li class="next"></li>
        </body></html>'''

    @patch('requests.sessions.Session.get')
    def test_scrape_two_pages(self, mock_get):
        # Configurar mock para devolver page1 y luego page2
        mock_get.side_effect = [Mock(status_code=200, text=self.page1), Mock(status_code=200, text=self.page2)]
        # Llamar a la función sin que intente escribir el archivo (parcheamos open)
        with patch('builtins.open', new_callable=unittest.mock.mock_open) as mock_file:
            result = scrape_all_quotes({})
        # Verificar resultados
        self.assertTrue(result['ok'])
        self.assertEqual(result['count'], 3)
        # Extraer los datos que fueron escritos en el archivo JSON
        written_json = ''.join(call.args[0] for call in mock_file().write.call_args_list)
        data = json.loads(written_json)
        self.assertEqual(len(data), 3)
        self.assertIn({'text': '“Life is what happens when you\'re busy making other plans.”', 'author': 'John Lennon'}, data)
        self.assertIn({'text': '“The greatest glory in living lies not in never falling, but in rising every time we fall.”', 'author': 'Nelson Mandela'}, data)
        self.assertIn({'text': '“To be yourself in a world that is constantly trying to make you something else is the greatest accomplishment.”', 'author': 'Ralph Waldo Emerson'}, data)

    @patch('requests.sessions.Session.get')
    def test_network_retry(self, mock_get):
        # Simular fallo en el primer intento y éxito en el segundo
        mock_get.side_effect = [requests.exceptions.ConnectionError('fail'), Mock(status_code=200, text=self.page1)]
        with patch('builtins.open', new_callable=unittest.mock.mock_open) as mock_file:
            result = scrape_all_quotes({})
        self.assertTrue(result['ok'])
        self.assertGreaterEqual(mock_get.call_count, 2)  # hubo al menos un reintento

# Fin del código de la herramienta
