def get_ai_news(args):
    """Obtiene noticias recientes sobre inteligencia artificial usando SerpAPI.
    Args:
        args (dict): Debe contener la clave 'api_key' (str).
    Returns:
        dict: {ok: bool, results?: list, error?: str, message?: str}
    """
    import requests
    # Validar API key
    api_key = args.get('api_key')
    if not isinstance(api_key, str) or not api_key.strip():
        return {"ok": False, "error": "API key inválida"}

    query = "inteligencia artificial"
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_news",
        "q": query,
        "api_key": api_key,
        "hl": "es",
        "num": "10"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Error de red: {str(e)}"}

    if response.status_code != 200:
        return {"ok": False, "error": f"Error HTTP {response.status_code}: {response.text}"}

    try:
        data = response.json()
    except ValueError:
        return {"ok": False, "error": "Respuesta no es JSON"}

    news_results = data.get("news_results", [])
    if not news_results:
        return {"ok": True, "results": [], "message": "No se encontraron noticias recientes"}

    results = []
    for item in news_results[:10]:
        results.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "source": item.get("source") or item.get("source_name"),
            "snippet": item.get("snippet")
        })

    return {"ok": True, "results": results}

    # --- Pruebas unitarias (no ejecutadas automáticamente) ---
    # Se incluyen como referencia para validar la robustez de la función.
    # import unittest
    # from unittest.mock import patch, Mock
    # class TestGetAiNews(unittest.TestCase):
    #     def setUp(self):
    #         self.api_key = "test_key"
    #
    #     @patch('requests.get')
    #     def test_successful_response(self, mock_get):
    #         mock_resp = Mock(status_code=200)
    #         mock_resp.json.return_value = {"news_results": [{"title": "AI News", "link": "http://example.com", "source": "Example", "snippet": "..."}]}
    #         mock_get.return_value = mock_resp
    #         result = get_ai_news({"api_key": self.api_key})
    #         self.assertTrue(result["ok"])
    #         self.assertEqual(len(result["results"]), 1)
    #
    #     @patch('requests.get')
    #     def test_http_error(self, mock_get):
    #         mock_resp = Mock(status_code=401, text='Unauthorized')
    #         mock_get.return_value = mock_resp
    #         result = get_ai_news({"api_key": self.api_key})
    #         self.assertFalse(result["ok"])
    #         self.assertIn('Error HTTP 401', result["error"])
    #
    #     @patch('requests.get', side_effect=requests.exceptions.RequestException('Timeout'))
    #     def test_network_exception(self, mock_get):
    #         result = get_ai_news({"api_key": self.api_key})
    #         self.assertFalse(result["ok"])
    #         self.assertIn('Error de red', result["error"])
    #
    # if __name__ == '__main__':
    #     unittest.main()
