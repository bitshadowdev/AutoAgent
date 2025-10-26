import re
import json
import requests
from bs4 import BeautifulSoup
import unittest
from unittest.mock import patch, MagicMock

class FactCheckerAgent:
    """Agent that verifies factuality of a given text using Wikipedia API.
    It splits the text into sentences, queries Wikipedia for each sentence
    and returns a structured report.
    """

    WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
    USER_AGENT = "FactCheckerAgent/1.0 (https://example.com)"
    TIMEOUT = 5  # seconds

    def _search_wikipedia(self, query: str) -> dict:
        """Search Wikipedia for the given query.
        Returns the JSON response from the API or an empty dict on failure.
        """
        try:
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "utf8": 1,
            }
            headers = {"User-Agent": self.USER_AGENT}
            resp = requests.get(self.WIKIPEDIA_API_URL, params=params, headers=headers, timeout=self.TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            # Propagate a simplified error structure
            return {"error": str(e)}

    def _extract_best_title(self, search_result: dict) -> str:
        """Extract the title of the first search result if available."""
        if "error" in search_result:
            return ""
        try:
            return search_result["query"]["search"][0]["title"]
        except (KeyError, IndexError):
            return ""

    def check_factuality(self, text: str) -> dict:
        """Check each sentence of *text* against Wikipedia.
        Returns a dict with two keys:
            - ok: bool indicating whether the operation succeeded.
            - report: list of dicts, one per sentence, with keys:
                * sentence: the original sentence string
                * verified: True if a Wikipedia page was found, False otherwise
                * source: the title of the found Wikipedia article (empty if none)
                * error: optional error message if the API call failed
        """
        if not text:
            return {"ok": False, "error": "Empty text provided."}
        # Split into sentences (very simple split on punctuation followed by space)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s]
        report = []
        for sentence in sentences:
            # Use a short snippet of the sentence as query (first 10 words)
            query = " ".join(sentence.split()[:10])
            search_res = self._search_wikipedia(query)
            if "error" in search_res:
                report.append({
                    "sentence": sentence,
                    "verified": False,
                    "source": "",
                    "error": search_res["error"]
                })
                continue
            title = self._extract_best_title(search_res)
            verified = bool(title)
            report.append({
                "sentence": sentence,
                "verified": verified,
                "source": title,
            })
        return {"ok": True, "report": report}

# ---------------------------------------------------------------------------
# Integration example – how the agent would be used in a generation pipeline
# ---------------------------------------------------------------------------

def generate_response_and_verify(prompt: str) -> dict:
    """Mock response generation (simply echoes the prompt) and runs factuality check.
    Returns the original response and the fact‑checking report.
    """
    # In a real system this would call an LLM. Here we just return the prompt.
    generated_text = prompt
    agent = FactCheckerAgent()
    check = agent.check_factuality(generated_text)
    # Decide if the response is approved (all sentences verified)
    approved = check.get("ok", False) and all(item.get("verified", False) for item in check.get("report", []))
    return {"response": generated_text, "approved": approved, "fact_check": check}

# ---------------------------------------------------------------------------
# Unit tests with mocking of the Wikipedia API
# ---------------------------------------------------------------------------

class TestFactCheckerAgent(unittest.TestCase):
    def setUp(self):
        self.agent = FactCheckerAgent()

    @patch('requests.get')
    def test_correct_statement(self, mock_get):
        # Mock a successful Wikipedia search returning a relevant title
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "query": {"search": [{"title": "Paris"}]}
        }
        mock_get.return_value = mock_resp
        text = "Paris is the capital of France."
        result = self.agent.check_factuality(text)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["report"]), 1)
        self.assertTrue(result["report"][0]["verified"])
        self.assertEqual(result["report"][0]["source"], "Paris")

    @patch('requests.get')
    def test_incorrect_statement(self, mock_get):
        # Mock a Wikipedia search with no results
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"query": {"search": []}}
        mock_get.return_value = mock_resp
        text = "The sun rises in the west."
        result = self.agent.check_factuality(text)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["report"]), 1)
        self.assertFalse(result["report"][0]["verified"])
        self.assertEqual(result["report"][0]["source"], "")

    @patch('requests.get')
    def test_network_error(self, mock_get):
        # Simulate a network failure
        mock_get.side_effect = requests.exceptions.ConnectionError("Network down")
        text = "Python is a programming language."
        result = self.agent.check_factuality(text)
        self.assertTrue(result["ok"])  # The function still returns ok=True because it handles the error per‑sentence
        self.assertEqual(len(result["report"]), 1)
        self.assertFalse(result["report"][0]["verified"])
        self.assertIn("Network down", result["report"][0]["error"])

    def test_empty_input(self):
        result = self.agent.check_factuality("")
        self.assertFalse(result["ok"])
        self.assertIn("Empty text provided", result["error"])

if __name__ == '__main__':
    unittest.main()
