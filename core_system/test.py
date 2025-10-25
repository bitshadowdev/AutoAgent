# sistema_agentes_supervisor_coder.py

"""
Sistema de agentes minimalista pero ***sin restricciones*** ("caja de Pandora").
Este archivo contiene la lógica principal de los agentes (Coder, Supervisor) y el orquestador (MiniAgentSystem).
El estado de la ejecución (transcript, herramientas) se gestiona de forma reactiva a través del módulo `agent_state`.
"""

from __future__ import annotations

import json
import re
import ast
import os
import sys
import argparse
from typing import Any, Dict, List, Optional

# ===============================
#  Import del sistema de estado y cliente LLM
# ===============================
from agent_state import ReactiveStateContainer, ToolSpec
try:
    from llm_client import CloudflareLLMClient
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from llm_client import CloudflareLLMClient
import requests


def _balanced_json_slice(text: str) -> Optional[str]:
    # ... (código sin cambios)
    i,n=0,len(text)
    while i<n and text[i]!='{':i+=1
    if i>=n:return None
    start,depth,in_str,str_ch,esc=i,0,False,'',False
    i-=1
    while i+1<n:
        i+=1
        ch=text[i]
        if in_str:
            if esc:esc=False;continue
            if ch=='\\':esc=True
            elif ch==str_ch:in_str=False
        else:
            if ch in ('"',"'"):in_str=True;str_ch=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return text[start:i+1]
    return None

def extract_json(text: str) -> Dict[str, Any]:
    # ... (código sin cambios)
    m=re.search(r"```json\s*(\{.*?\})\s*```",text,flags=re.DOTALL|re.IGNORECASE)
    candidate=m.group(1) if m else _balanced_json_slice(text)
    if not candidate:raise ValueError("No se encontró JSON en la respuesta del LLM:\n"+text[:600])
    try:return json.loads(candidate)
    except json.JSONDecodeError:
        try:
            value=ast.literal_eval(candidate)
            if isinstance(value,dict):return value
        except Exception as e:raise ValueError(f"No se pudo parsear JSON: {e}\nContenido:\n{candidate[:600]}")
        raise ValueError("El bloque extraído no es un objeto JSON (dict).")

# ===============================
#  Prompts (sin cambios)
# ===============================
CODER_SYSTEM = """
Eres el *Agente Programador*.
Resuelve la tarea de la forma más simple y confiable posible.

Puedes:
- Responder directamente (type='final'), o
- Crear una herramienta Python y llamarla (type='create_tool'), o
- Llamar una herramienta previamente creada (type='call_tool').

Reglas de herramienta (MODO ABIERTO):
- **Se permiten `import`**, dunders, red (HTTP), sistema de archivos, uso de `subprocess` (p. ej. `pip`).
- La función debe llamarse exactamente como 'tool.name'.
- Firma: `def <name>(args: dict) -> (dict|list|str|int|float|bool)`.
- Devuelve **solo valores JSON-serializables**. Si lees binarios, devuélvelos codificados (p. ej. base64) o a disco y retorna la ruta.
- Si haces scraping, intenta respetar robots.txt y Términos del sitio.

Salida: SOLO JSON válido, uno de:

(1) Final:
{
  "type": "final",
  "message": "breve explicación",
  "answer": "texto para el usuario"
}

(2) Crear y llamar:
{
  "type": "create_tool",
  "message": "por qué se crea",
  "tool": {
    "name": "nombre_funcion",
    "code": "def nombre_funcion(args):\\n    ...\\n    return {...}"
  },
  "call": {
    "name": "nombre_funcion",
    "args": {"clave": "valor"}
  }
}

(3) Solo llamar existente:
{
  "type": "call_tool",
  "message": "qué va a hacer",
  "call": {
    "name": "nombre_funcion",
    "args": {"clave": "valor"}
  }
}
"""
SUPERVISOR_SYSTEM = """
Eres el *Supervisor*.
Evalúa si la salida satisface la tarea. Devuelve SOLO JSON:
{
  "route": "end" | "coder",
  "reason": "breve justificación",
  "tips": ["consejo 1", "consejo 2", "consejo 3"]  // 3–6 sugerencias accionables para el próximo paso
}

Criterio:
- Si hay una respuesta clara/útil -> end.
- Si falta completar/mejorar -> coder.

Guía para 'tips':
- Sé específico y verificable (p.ej., “agrega pruebas para X”, “maneja error Y”, “cubre caso límite Z”).
- Incluye, cuando aplique: siguiente acción, cómo validarla, y un criterio de salida.
- Enfoca en brechas observables: pruebas, manejo de errores, casos límite, rendimiento, seguridad, UX, fuentes/citas, estructura del código.
"""

# ===============================
#  Agentes (sin cambios)
# ===============================
# Nota: No necesitamos cambiar nada aquí. Los agentes seguirán llamando a `llm.chat`
# como antes, pero la instancia de `llm` que les pasaremos será nuestro Adaptador.
class CoderAgent:
    def __init__(self, llm: CloudflareLLMClient, model: Optional[str] = None):
        self.llm = llm
        self.model = model or os.environ.get('CF_MODEL', '@cf/meta/llama-3-8b-instruct')

    def step(self, task: str, transcript: List[Dict[str, str]]) -> Dict[str, Any]:
        messages = [{"role": "system", "content": CODER_SYSTEM}, *transcript, {"role": "user", "content": f"Tarea: {task}\n\nResponde SOLO con JSON."}]
        # Esta llamada ahora irá al método `chat` del Adaptador
        raw = self.llm.chat(messages, model=self.model, temperature=0.2, max_tokens=2048)
        return extract_json(raw)

class Supervisor:
    def __init__(self, llm: CloudflareLLMClient, model: Optional[str] = None):
        self.llm = llm
        self.model = model or os.environ.get('CF_MODEL', '@cf/meta/llama-3-8b-instruct')

    def decide(self, task: str, transcript: List[Dict[str, str]]) -> Dict[str, Any]:
        messages = [{"role": "system", "content": SUPERVISOR_SYSTEM}, *transcript, {"role": "user", "content": f"Tarea original: {task}\n\n¿Terminar o derivar? Devuelve SOLO JSON."}]
        # Esta llamada también irá al método `chat` del Adaptador
        raw = self.llm.chat(messages, model=self.model, temperature=0.0, max_tokens=512)
        return extract_json(raw)

# ===============================
#  Orquestador (Actualizado para usar estado externo)
# ===============================
class MiniAgentSystem:
    def __init__(self, llm: CloudflareLLMClient, state: ReactiveStateContainer):
        self.llm = llm
        self.coder = CoderAgent(llm)
        self.supervisor = Supervisor(llm)
        self.state = state

    def _print_turn(self, msg: Dict[str, str]) -> None:
        role = msg.get("role", "").upper()
        content = msg.get("content", "")
        print(f"\n[{role}] {content}")

    def run(self, task: str, max_turns: int = 5, stream: bool = True) -> Dict[str, Any]:
        self.state.reset_transcript()
        self.state.set_task(task)

        for turn in range(max_turns):
            print(f"\n--- Turno {turn + 1}/{max_turns} ---")
            try:
                coder_out = self.coder.step(self.state.task, self.state.transcript)
            except Exception as e:
                self.state.transcript.append({'role': 'assistant', 'content': f"[Coder] Error en la llamada al LLM o al parsear su salida: {e}"})
                if stream: self._print_turn(self.state.transcript[-1])
                self.state.transcript.append({'role': 'user', 'content': '[Supervisor] Hubo un error. Por favor, reintenta generando un JSON válido.'})
                if stream: self._print_turn(self.state.transcript[-1])
                continue

            ctype = (coder_out.get('type') or '').lower()

            if ctype == 'final':
                content = f"[Coder] {coder_out.get('message', '')}\n\nRespuesta propuesta:\n{coder_out.get('answer', '')}"
                self.state.transcript.append({'role': 'assistant', 'content': content})
                if stream: self._print_turn(self.state.transcript[-1])
            elif ctype in ('create_tool', 'call_tool'):
                call = coder_out.get('call', {})
                name = str(call.get('name', ''))
                args = call.get('args', {})

                if ctype == 'create_tool':
                    tool_data = coder_out.get('tool', {})
                    tname = tool_data.get('name', name)
                    code = str(tool_data.get('code', ''))
                    if not self.state.tool_registry.has(tname):
                        spec = ToolSpec(name=tname, code=code)
                        self.state.tool_registry.add(spec)
                        print(f"\n[SISTEMA] Herramienta '{tname}' creada y registrada.")
                    name = tname
                
                result = self.state.tool_registry.call(name, args)
                content = f"[Coder] {coder_out.get('message', '')}\n\nTool: {name}\nArgs: {args}\nResult: {result}"
                self.state.transcript.append({'role': 'assistant', 'content': content})
                if stream: self._print_turn(self.state.transcript[-1])
                
                if isinstance(result, dict) and result.get("ok") is False:
                    tb = (result.get("traceback") or "")[:1200]
                    feedback = f"[Supervisor] La herramienta '{name}' falló: {result.get('error')}. Corrige y reintenta.\nTraceback:\n{tb}"
                    self.state.transcript.append({'role': 'user', 'content': feedback})
                    if stream: self._print_turn(self.state.transcript[-1])
            else:
                self.state.transcript.append({'role': 'assistant', 'content': f"[Coder] Tipo de salida desconocido: {ctype}."})
                if stream: self._print_turn(self.state.transcript[-1])
            
            try:
                decision = self.supervisor.decide(self.state.task, self.state.transcript)
                route = (decision.get('route') or '').lower()
            except Exception as e:
                route = 'coder'
                self.state.transcript.append({'role': 'assistant', 'content': f"[Supervisor] Error en decisión: {e}. Continuar."})
                if stream: self._print_turn(self.state.transcript[-1])

            if route == 'end':
                last = next((m for m in reversed(self.state.transcript) if m['role'] == 'assistant'), {'content': 'Tarea finalizada.'})
                return {"final": last['content'], "state": self.state.to_dict()}
            
            feedback = f"[Supervisor] {decision.get('reason', 'Continúa')}\nConsejos: {decision.get('tips', ['Mejorar la respuesta.'])}"
            self.state.transcript.append({'role': 'user', 'content': feedback})
            if stream: self._print_turn(self.state.transcript[-1])

        last = next((m for m in reversed(self.state.transcript) if m['role'] == 'assistant'), {'content': 'No se completó en los turnos permitidos.'})
        return {"final": last['content'], "state": self.state.to_dict()}

# ===============================
#  Ejecución directa (MODIFICADO)
# ===============================
# ===============================
#  CLASE ADAPTADORA PARA CORREGIR EL PAYLOAD (VERSIÓN 2 - ROBUSTA)
# ===============================

# Importamos 'requests' si no está ya disponible globalmente
import requests

class CloudflareClientAdapter(CloudflareLLMClient):
    """
    Clase adaptadora que reimplementa `chat` para garantizar el formato correcto.

    Hereda de CloudflareLLMClient para reutilizar la configuración (URL, tokens)
    del __init__, pero sobrescribe `chat` con una implementación robusta que:
    1. Construye el payload correcto: `{"messages": [...]}`.
    2. Realiza la llamada a la API directamente usando `requests`.
    3. Parsea la respuesta de la API y devuelve únicamente el contenido de texto del LLM.
    """
    def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        # La URL se construye a partir de los atributos heredados de la clase padre
        url = f"{self.base_url}/{self.account_id}/{model}"

        # El payload se construye correctamente, como requiere la API
        payload = {"messages": messages}
        
        # Combinamos los kwargs (temperature, max_tokens) en el payload si existen
        payload.update(kwargs)

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()  # Lanza un error para códigos 4xx/5xx

            response_data = response.json()

            if not response_data.get("success"):
                errors = response_data.get("errors", "Errores desconocidos")
                raise Exception(f"La API de Cloudflare devolvió un error: {errors}")

            # Extraemos y devolvemos la cadena de texto de la respuesta del LLM
            return response_data.get("result", {}).get("response", "")

        except requests.exceptions.RequestException as e:
            # Capturamos errores de red o HTTP y los relanzamos
            raise Exception(f"Error en la llamada al LLM: {e}")
        except json.JSONDecodeError:
            # Capturamos el caso en que la respuesta no sea un JSON válido
            raise Exception(f"La respuesta de la API no era un JSON válido: {response.text}")


# ... (el resto del archivo, CoderAgent, Supervisor, MiniAgentSystem, etc., permanece igual) ...

# sistema_agentes_supervisor_coder.py

# ... (todos los imports, prompts y clases de agentes sin cambios) ...

# ===============================
#  Ejecución directa (LIMPIO Y FUNCIONAL)
# ===============================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mini sistema de agentes reactivo y persistente.')
    parser.add_argument('-t', '--task', dest='task', help='Tarea a resolver.')
    parser.add_argument('-m', '--max-turns', dest='max_turns', type=int, default=5, help='Máximo de turnos.')
    parser.add_argument('-c', '--checkpoint-path', dest='checkpoint_path', default="agent_state.json", help='Ruta al archivo de estado (checkpoint).')
    args = parser.parse_args()

    state_container = ReactiveStateContainer.load_checkpoint(args.checkpoint_path)

    # Volvemos a usar el cliente original, que ahora está corregido.
    # ¡Ya no necesitamos el adaptador!
    llm = CloudflareLLMClient()
    
    system = MiniAgentSystem(llm, state=state_container)

    tarea = (
        args.task
        or os.environ.get('AGENT_TASK')
        or input('Escribe tu pregunta/tarea: ').strip()
        or 'Dame una lista de las top 10 canciones en las listas internacionales.'
    )

    resultado = system.run(tarea, max_turns=args.max_turns)
    print('\n\n' + '='*20 + ' RESPUESTA FINAL ' + '='*20)
    print(resultado['final'])
    print(f"\n[SISTEMA] El estado final de la ejecución ha sido guardado en '{args.checkpoint_path}'")