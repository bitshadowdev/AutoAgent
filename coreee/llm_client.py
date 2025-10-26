"""
Cliente LLM para Cloudflare Workers AI
"""
import os
import requests
from requests.adapters import HTTPAdapter, Retry
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()


class CloudflareLLMClient:
    """Cliente para interactuar con Cloudflare Workers AI"""
    
    def __init__(self):
        self.account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        self.auth_token = os.environ.get("CLOUDFLARE_AUTH_TOKEN")
        
        if not self.account_id or not self.auth_token:
            raise ValueError("Faltan credenciales de Cloudflare. Configura CLOUDFLARE_ACCOUNT_ID y CLOUDFLARE_AUTH_TOKEN en .env")
        
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/v1/responses"
        self._session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Crea una sesión con reintentos automáticos."""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.6,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
        
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "@cf/openai/gpt-oss-120b",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Envía mensajes al LLM y obtiene una respuesta
        
        Args:
            messages: Lista de mensajes en formato [{"role": "system/user/assistant", "content": "..."}]
            model: Modelo a usar
            temperature: Temperatura para generación (0.0 - 1.0)
            max_tokens: Número máximo de tokens
            
        Returns:
            Respuesta del modelo como string
        """
        # Convertir mensajes al formato de Cloudflare
        # Cloudflare Workers AI acepta un input simple o mensajes estructurados
        prompt = self._format_messages(messages)
        
        # VALIDACIÓN CRÍTICA: Evitar prompts vacíos/nulos
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt vacío o inválido para Cloudflare. El prompt debe ser un string no vacío.")
        
        payload = {
            "model": model,
            "input": prompt
        }
        
        # Agregar parámetros opcionales si el endpoint los soporta
        # (Nota: Cloudflare Workers AI puede tener limitaciones en parámetros)
        
        try:
            response = self._session.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json=payload,
                timeout=(5, 60)  # (connection timeout, read timeout)
            )
        except requests.exceptions.Timeout:
            raise Exception("Timeout al llamar al LLM. El servidor no respondió a tiempo.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de red al llamar al LLM: {e}")
        
        if response.status_code != 200:
            raise Exception(f"Error al llamar al LLM: {response.status_code} - {response.text}")
        
        result = response.json()

        # Extraer la respuesta del resultado según distintas formas del API
        # 1) Formato antiguo: { result: { response: "..." } }
        if isinstance(result, dict) and "result" in result:
            inner = result.get("result", {})
            if isinstance(inner, dict) and "response" in inner:
                return inner.get("response", "")
            # Si no hay "response", devolver como string para fallback
            return str(inner)

        # 2) Formato Responses API: top-level con 'output' (lista de pasos)
        # Buscamos un item de tipo 'message' y dentro su 'content' de tipo 'output_text'
        if isinstance(result, dict) and "output" in result and isinstance(result["output"], list):
            for step in result["output"]:
                if isinstance(step, dict) and step.get("type") == "message":
                    contents = step.get("content", [])
                    if isinstance(contents, list):
                        for c in contents:
                            if isinstance(c, dict) and c.get("type") == "output_text":
                                text = c.get("text")
                                if isinstance(text, str):
                                    return text
            # Si no encontramos, intentar 'text' top-level
            if isinstance(result.get("text"), str):
                return result["text"]

        # 3) Fallback: si hay 'text' directamente
        if isinstance(result, dict) and isinstance(result.get("text"), str):
            text = result["text"]
            if text.strip():
                return text
        
        # 4) Validación: si no encontramos ningún output válido
        # Retornar error estructurado en lugar de string vacío
        if not result or (isinstance(result, dict) and not any(result.values())):
            return '{"ok": false, "code": "LLM_OUTPUT_EMPTY", "error": "El LLM no generó ninguna respuesta válida."}'

        # Último recurso: convertir todo a string
        result_str = str(result)
        if not result_str.strip():
            return '{"ok": false, "code": "LLM_OUTPUT_EMPTY", "error": "El LLM retornó un resultado vacío."}'
        return result_str
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Formatea los mensajes en un prompt simple
        
        Args:
            messages: Lista de mensajes
            
        Returns:
            Prompt formateado
        """
        formatted = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                formatted.append(f"Sistema: {content}")
            elif role == "user":
                formatted.append(f"Usuario: {content}")
            elif role == "assistant":
                formatted.append(f"Asistente: {content}")
        
        return "\n\n".join(formatted)
