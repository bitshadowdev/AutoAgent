import re
import json
import requests
from typing import List, Dict, Any

class FactCheckerAgent:
    """Agente que verifica la factualidad de un texto usando la API de Wikipedia.

    Métodos
    -------
    check_factuality(text: str) -> Dict[str, Any]
        Devuelve un reporte con la verificación de cada oración.
    """

    WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
    USER_AGENT = "FactCheckerAgent/1.0 (https://github.com/yourrepo)"
    TIMEOUT = 10  # segundos

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

    def _search_wikipedia(self, query: str) -> Dict[str, Any]:
        """Realiza una búsqueda en Wikipedia y devuelve el primer resultado.

        Parámetros
        ----------
        query: str
            Texto a buscar.
        """
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1,
        }
        try:
            resp = self.session.get(self.WIKI_API_URL, params=params, timeout=self.TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            search_results = data.get("query", {}).get("search", [])
            if not search_results:
                return {"found": False}
            first = search_results[0]
            pageid = first.get("pageid")
            title = first.get("title")
            # Construir URL de la página
            url = f"https://en.wikipedia.org/?curid={pageid}"
            return {"found": True, "title": title, "url": url}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def _verify_sentence(self, sentence: str) -> Dict[str, Any]:
        """Verifica una oración mediante búsqueda en Wikipedia.

        Devuelve un dict con claves:
        - sentence: la oración original
        - verified: bool indicando si se encontró evidencia
        - source: URL de la fuente (si la hay)
        - error: mensaje de error (si lo hubo)
        """
        if not sentence.strip():
            return {"sentence": sentence, "verified": False, "source": None, "error": "Oración vacía"}
        search = self._search_wikipedia(sentence)
        if "error" in search:
            return {"sentence": sentence, "verified": False, "source": None, "error": search["error"]}
        if search.get("found"):
            # Consideramos verificado si el título contiene alguna palabra clave importante de la oración.
            # Simplificamos usando intersección de palabras (sin stopwords).
            words = set(re.findall(r"\w+", sentence.lower()))
            title_words = set(re.findall(r"\w+", search["title"].lower()))
            intersect = words & title_words
            verified = len(intersect) >= 2  # al menos dos palabras en común
            return {
                "sentence": sentence,
                "verified": verified,
                "source": search["url"] if verified else None,
                "error": None if verified else "No hay coincidencia suficiente en Wikipedia",
            }
        else:
            return {"sentence": sentence, "verified": False, "source": None, "error": "No se encontró información"}

    def check_factuality(self, text: str) -> Dict[str, Any]:
        """Analiza el texto, verifica cada sentencia y devuelve un reporte.

        Parámetros
        ----------
        text: str
            Texto a verificar.
        """
        if not isinstance(text, str) or not text.strip():
            return {"ok": False, "error": "Texto vacío o no válido"}
        # Dividir en oraciones (simplemente por punto, signo de exclamación o interrogación)
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        report: List[Dict[str, Any]] = []
        for s in sentences:
            if s:
                result = self._verify_sentence(s)
                report.append(result)
        return {"ok": True, "report": report}

# ---------- Pruebas unitarias ----------
import unittest

class TestFactCheckerAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = FactCheckerAgent()

    def test_correct_statement(self):
        text = "Paris is the capital of France."
        res = self.agent.check_factuality(text)
        self.assertTrue(res["ok"])
        self.assertTrue(res["report"][0]["verified"])
        self.assertIsNotNone(res["report"][0]["source"])

    def test_incorrect_statement(self):
        text = "The sun rises in the west."
        res = self.agent.check_factuality(text)
        self.assertTrue(res["ok"])
        self.assertFalse(res["report"][0]["verified"])
        self.assertIsNone(res["report"][0]["source"])
        self.assertIsNotNone(res["report"][0]["error"])

    def test_no_source_available(self):
        # Usamos una cadena aleatoria poco probable que exista en Wikipedia
        text = "Xyzzy blorg flarp."
        res = self.agent.check_factuality(text)
        self.assertTrue(res["ok"])
        self.assertFalse(res["report"][0]["verified"])
        self.assertIsNone(res["report"][0]["source"])
        self.assertEqual(res["report"][0]["error"], "No se encontró información")

    def test_empty_text(self):
        res = self.agent.check_factuality("")
        self.assertFalse(res["ok"])
        self.assertIn("error", res)

    def test_network_error_handling(self):
        # Simulamos error de red sobrescribiendo la sesión temporalmente
        original_session = self.agent.session
        class BadSession:
            def get(self, *args, **kwargs):
                raise requests.exceptions.ConnectionError("Simulated connection error")
        self.agent.session = BadSession()
        res = self.agent.check_factuality("Paris is the capital of France.")
        self.assertTrue(res["ok"])  # La función sigue devolviendo ok=True, pero el reporte indica error
        self.assertFalse(res["report"][0]["verified"])
        self.assertIn("Simulated connection error", res["report"][0]["error"])
        # Restaurar sesión original
        self.agent.session = original_session

if __name__ == "__main__":
    unittest.main(argv=["-v"], exit=False)

def run_fact_checker(args: dict) -> dict:
    """Función expuesta como herramienta.

    Parámetros esperados en *args*:
    - "text": str, texto a verificar.

    Devuelve un dict con claves:
    - ok: bool
    - report: list de dicts con la verificación (solo si ok=True)
    - error: mensaje de error (solo si ok=False)
    """
    try:
        text = args.get("text", "")
        agent = FactCheckerAgent()
        result = agent.check_factuality(text)
        return result
    except Exception as e:
        return {"ok": False, "error": f"Excepción inesperada: {str(e)}"}
