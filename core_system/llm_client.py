# llm_client.py

"""
Cliente LLM para Cloudflare Workers AI, actualizado para usar el endpoint de Chat.
"""
import os
import requests
import json
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()


class CloudflareLLMClient:
    """Cliente para interactuar con los modelos de chat de Cloudflare Workers AI."""

    def __init__(self):
        self.account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        self.auth_token = os.environ.get("CLOUDFLARE_AUTH_TOKEN")

        if not self.account_id or not self.auth_token:
            raise ValueError(
                "Faltan credenciales de Cloudflare. "
                "Configura CLOUDFLARE_ACCOUNT_ID y CLOUDFLARE_AUTH_TOKEN en .env"
            )

        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run"
        self.headers = {"Authorization": f"Bearer {self.auth_token}"}

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "@cf/meta/llama-3-8b-instruct",
        **kwargs,
    ) -> str:
        """
        Envía mensajes a un modelo de chat de Cloudflare y obtiene una respuesta.

        Args:
            messages: Lista de mensajes en formato [{"role": "system/user/assistant", "content": "..."}]
            model: Nombre completo del modelo a usar (ej. "@cf/meta/llama-3-8b-instruct")
            **kwargs: Otros parámetros para el modelo como temperature, max_tokens, etc.

        Returns:
            Respuesta del modelo como una cadena de texto.
        """
        # El endpoint para modelos de chat incluye el nombre del modelo
        url = f"{self.base_url}/{model}"

        # El payload para los modelos de chat es un diccionario con la clave "messages"
        payload = {
            "messages": messages
        }
        
        # Añadir cualquier otro parámetro opcional (temperature, max_tokens) al payload
        if kwargs:
            payload.update(kwargs)

        try:
            response = requests.post(url, headers=self.headers, json=payload)

            # Lanza una excepción para códigos de error HTTP (4xx o 5xx)
            response.raise_for_status()

            response_data = response.json()

            # Verificamos si la respuesta de la API fue exitosa
            if not response_data.get("success"):
                errors = response_data.get("errors", "Error desconocido en la respuesta de la API")
                raise Exception(f"La API de Cloudflare indicó un fallo: {errors}")

            # La respuesta del modelo de chat está en result.response
            return response_data.get("result", {}).get("response", "")

        except requests.exceptions.RequestException as e:
            # Capturamos errores de red, timeouts, etc.
            error_details = e.response.text if e.response else str(e)
            raise Exception(f"Error al llamar al LLM: {error_details}")
        except json.JSONDecodeError:
            # Capturamos el caso en que la respuesta no sea un JSON válido
            raise Exception(f"La respuesta de la API no era un JSON válido: {response.text}")