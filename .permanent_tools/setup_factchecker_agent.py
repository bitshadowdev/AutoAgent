def setup_factchecker_agent(args):
    import re
    import requests
    import json
    from bs4 import BeautifulSoup
    import unittest
    from unittest.mock import patch

    class FactCheckerAgent:
        USER_AGENT = "FactCheckerAgent/1.0 (https://example.com)"
        WIKI_API_URL = "https://en.wikipedia.org/w/api.php"

        def _search_wikipedia(self, query):
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "utf8": 1,
            }
            headers = {"User-Agent": self.USER_AGENT}
            resp = requests.get(self.WIKI_API_URL, params=params, headers=headers, timeout=5)
            resp.raise_for_status()
            return resp.json()

        def check_factuality(self, text):
            if not text:
                return {"ok": False, "error": "Empty text", "report": None}
            # Split text into sentences (simple heuristic)
            sentences = re.split(r'(?<=[.!?])\s+', text.strip())
            report = []
            for s in sentences:
                claim = s.strip()
                try:
                    data = self._search_wikipedia(claim)
                    hits = data.get("query", {}).get("search", [])
                    verified = bool(hits)
                    source = hits[0]["title"] if verified else None
                except requests.exceptions.RequestException as e:
                    return {"ok": False, "error": f"Network error: {e}", "report": None}
                report.append({"sentence": claim, "verified": verified, "source": source})
            return {"ok": True, "report": report}

    # Integración de ejemplo: genera texto y lo verifica
    def generate_and_check(response_text):
        agent = FactCheckerAgent()
        result = agent.check_factuality(response_text)
        approved = result.get("ok") and all(r["verified"] for r in result.get("report", []))
        return {"approved": approved, "result": result}

    # --- Unit tests ---
    class TestFactCheckerAgent(unittest.TestCase):
        def setUp(self):
            self.agent = FactCheckerAgent()

        @patch('requests.get')
        def test_correct_statement(self, mock_get):
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "query": {"search": [{"title": "Paris"}]}
            }
            text = "Paris is the capital of France."
            res = self.agent.check_factuality(text)
            self.assertTrue(res["ok"])
            self.assertTrue(res["report"][0]["verified"])

        @patch('requests.get')
        def test_incorrect_statement(self, mock_get):
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"query": {"search": []}}
            text = "The sun rises in the west."
            res = self.agent.check_factuality(text)
            self.assertTrue(res["ok"])
            self.assertFalse(res["report"][0]["verified"])

        @patch('requests.get')
        def test_no_source_available(self, mock_get):
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"query": {"search": []}}
            text = "Xyzabc is a mythical creature."
            res = self.agent.check_factuality(text)
            self.assertTrue(res["ok"])
            self.assertFalse(res["report"][0]["verified"])

    # Ejecutar pruebas unitarias
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestFactCheckerAgent)
    runner = unittest.TextTestRunner()
    test_result = runner.run(suite)

    if test_result.wasSuccessful():
        example = generate_and_check("Paris is the capital of France. The sun rises in the west.")
        return {"ok": True, "message": "All tests passed.", "integration_example": example}
    else:
        return {"ok": False, "error": "Unit tests failed."}