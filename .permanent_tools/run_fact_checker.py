import re
import json
import requests
from typing import List, Dict

class FactCheckerAgent:
    """Agente que verifica la factualidad de un texto usando la API pública de Wikipedia.
    
    Cada oración del texto se busca en Wikipedia. Si la búsqueda devuelve al menos un
    artículo relevante, la oración se marca como verificada y se incluye el título del
    artículo como fuente. En caso contrario se marca como no verificada.
    """
    WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
    USER_AGENT = "FactCheckerAgent/1.0 (https://example.com; contact@example.com)"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

    def _search_wikipedia(self, query: str) -> Dict:
        """Realiza una búsqueda en Wikipedia y devuelve el primer resultado (si lo hay)."""
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1,
            "srlimit": 1,
        }
        try:
            resp = self.session.get(self.WIKIPEDIA_API_URL, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            search_results = data.get("query", {}).get("search", [])
            if search_results:
                return search_results[0]  # primer artículo encontrado
            return {}
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error de red al consultar Wikipedia: {e}")
        except (ValueError, KeyError) as e:
            raise RuntimeError(f"Error al procesar la respuesta de Wikipedia: {e}")

    def _split_sentences(self, text: str) -> List[str]:
        """Divide el texto en oraciones usando una expresión regular simple."""
        # Esta expresión separa por puntos, signos de exclamación o interrogación seguidos de espacio.
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        # Elimina oraciones vacías
        return [s.strip() for s in sentences if s.strip()]

    def check_factuality(self, text: str) -> Dict:
        """Comprueba la factualidad de cada oración del texto.
        Devuelve un reporte estructurado:
        {
            "ok": bool,
            "report": [
                {"sentence": str, "verified": bool, "source": str|None}, ...
            ],
            "error": str|None
        }
        """
        if not text:
            return {"ok": False, "report": None, "error": "Texto vacío recibido."}
        report = []
        try:
            sentences = self._split_sentences(text)
            for sentence in sentences:
                # Usamos la oración completa como consulta
                result = self._search_wikipedia(sentence)
                if result:
                    report.append({
                        "sentence": sentence,
                        "verified": True,
                        "source": result.get("title")
                    })
                else:
                    report.append({
                        "sentence": sentence,
                        "verified": False,
                        "source": None
                    })
            return {"ok": True, "report": report, "error": None}
        except Exception as e:
            return {"ok": False, "report": None, "error": str(e)}

def run_fact_checker(args: dict) -> dict:
    """Función de entrada de la herramienta.
    Espera {'text': <str>} y devuelve el reporte del agente.
    """
    text = args.get('text', '')
    agent = FactCheckerAgent()
    return agent.check_factuality(text)

# ---------------------------------------------------------------------------
# Herramienta para ejecutar pruebas unitarias del agente
# ---------------------------------------------------------------------------
import unittest

class TestFactCheckerAgent(unittest.TestCase):
    def setUp(self):
        self.agent = FactCheckerAgent()

    def test_correct_statement(self):
        # "Paris is the capital of France." está presente en Wikipedia
        text = "Paris is the capital of France."
        result = self.agent.check_factuality(text)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["report"]), 1)
        self.assertTrue(result["report"][0]["verified"])
        self.assertIsNotNone(result["report"][0]["source"])

    def test_incorrect_statement(self):
        # "The sun rises in the west." no es cierto y no debe aparecer como artículo relevante
        text = "The sun rises in the west."
        result = self.agent.check_factuality(text)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["report"]), 1)
        self.assertFalse(result["report"][0]["verified"])
        self.assertIsNone(result["report"][0]["source"])

    def test_no_source_available(self):
        # Una frase sin sentido debería no ser encontrada
        text = "Xyzzy is a fictional creature."
        result = self.agent.check_factuality(text)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["report"]), 1)
        self.assertFalse(result["report"][0]["verified"])
        self.assertIsNone(result["report"][0]["source"])

def run_fact_checker_tests(_: dict) -> dict:
    """Ejecuta los tests unitarios y devuelve un resumen JSON.
    No necesita argumentos.
    """
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFactCheckerAgent)
    runner = unittest.TextTestRunner(stream=open('/dev/null', 'w'), verbosity=2)
    result = runner.run(suite)
    summary = {
        "total": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "passed": result.testsRun - len(result.failures) - len(result.errors)
    }
    return summary
