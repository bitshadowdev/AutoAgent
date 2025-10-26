"""
Sistema de agentes (Supervisor + Coder) con **tools persistentes** en disco.

Novedades clave (persistencia):
- Las herramientas creadas por el Coder se guardan en un directorio persistente (por defecto: `.permanent_tools` o `TOOL_STORE_DIR`).
- En cada ejecución, el sistema **carga automáticamente** todas las tools guardadas previamente.
- Manifest de tools con versionado ligero y timestamps.
- API para listar tools disponibles.

Seguridad: este modo sigue siendo **abierto** (imports, red, FS, subprocess). Úsalo en entornos controlados.

Requisitos:
- Python 3.9+
- Archivo `llm_client.py` (Cloudflare Workers AI).
- .env con `CLOUDFLARE_ACCOUNT_ID` y `CLOUDFLARE_AUTH_TOKEN`.
- Opcional: `TOOL_STORE_DIR` para cambiar la carpeta de tools persistentes.

Ejecutar:
    python sistema_agentes_supervisor_coder.py -q "tu tarea"
    # Opcional
    python sistema_agentes_supervisor_coder.py --tools-list
"""

from __future__ import annotations

import json
import re
import ast
import os
import sys
from typing import Any, Callable, Dict, List, Optional
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from time import perf_counter
from copy import deepcopy
import asyncio

# Agregar el directorio padre al PYTHONPATH para imports absolutos
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# ===============================
#  Imports adicionales
# ===============================
# Imports absolutos desde el paquete coreee
from coreee.llm_client import CloudflareLLMClient
from coreee.enhanced_recorder import EnhancedRecorder
from coreee.session_manager import SessionManager
from coreee.agent_registry import AgentRegistry

# ===============================
#  Utilidades
# ===============================

def _balanced_json_slice(text: str) -> Optional[str]:
    """Extrae un slice balanceado { ... } respetando strings y escapes."""
    i, n = 0, len(text)
    while i < n and text[i] != '{':
        i += 1
    if i >= n:
        return None
    start, depth, in_str, str_ch, esc = i, 0, False, '', False
    i -= 1
    while i + 1 < n:
        i += 1
        ch = text[i]
        if in_str:
            if esc:
                esc = False
                continue
            if ch == '\\':
                esc = True
            elif ch == str_ch:
                in_str = False
        else:
            if ch in ('"', "'"):
                in_str = True
                str_ch = ch
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start: i + 1]
    return None


def extract_json(text: str) -> Dict[str, Any]:
    """Extrae el primer objeto JSON válido desde texto.
    Acepta bloques ```json ... ``` o la primera región balanceada { ... }.
    Hace fallback a ast.literal_eval para dicts con comillas simples.
    """
    # 1) Bloque con triple backticks
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    candidate: Optional[str] = m.group(1) if m else None

    # 2) Primer bloque { ... } balanceado
    if not candidate:
        candidate = _balanced_json_slice(text)

    if not candidate:
        raise ValueError("No se encontró JSON en la respuesta del LLM:\n" + text[:600])

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        try:
            value = ast.literal_eval(candidate)
            if isinstance(value, dict):
                return value
        except Exception as e:
            raise ValueError(f"No se pudo parsear JSON: {e}\nContenido capturado:\n{candidate[:600]}")
        raise ValueError("El bloque extraído no es un objeto JSON (dict).")


# ===============================
#  Motor de Diagnósticos (reglas → código + acción)
# ===============================

DIAGNOSTIC_RULES = [
    {
        "code": "PY_NAMEERROR_IMPORT",
        "pattern": r"NameError: name '(\w+)' is not defined",
        "category": "imports",
        "hint": "Falta importar '{m1}'. Agrega `import {m1}` al inicio del código.",
        "action": {"type": "suggest_fix_import", "module": "{m1}"}
    },
    {
        "code": "HTTP_404_VOICE_NOT_FOUND",
        "pattern": r"voice_not_found",
        "category": "api",
        "hint": "El voice_id no existe en tu cuenta. Lista voces y reintenta.",
        "action": {"type": "call_helper", "helper": "elevenlabs_list_voices"}
    },
    {
        "code": "CF_INVALID_PROMPT_NONE",
        "pattern": r"'NoneType' object has no attribute 'startswith'",
        "category": "llm",
        "hint": "Se envió prompt vacío/nulo al LLM. Valida prompt antes de llamar.",
        "action": {"type": "guard", "guard": "non_empty_prompt"}
    },
    {
        "code": "JSON_FORMAT_INVALID",
        "pattern": r"No se pudo parsear JSON|No se encontró JSON",
        "category": "format",
        "hint": "La salida del modelo no es JSON válido. Forzar bloque ```json y objeto plano.",
        "action": {"type": "prompt_fix", "target": "coder_json"}
    },
    {
        "code": "PY_IMPORTERROR",
        "pattern": r"ImportError: No module named '(\w+)'|ModuleNotFoundError: No module named '(\w+)'",
        "category": "imports",
        "hint": "El módulo '{m1}' no está instalado. Instálalo con 'pip install {m1}'.",
        "action": {"type": "suggest_install", "package": "{m1}"}
    }
]


def diagnose(text: str) -> Optional[Dict[str, Any]]:
    """Analiza un mensaje de error y retorna diagnóstico con acción sugerida."""
    for r in DIAGNOSTIC_RULES:
        m = re.search(r["pattern"], text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            params = {f"m{i}": m.group(i) for i in range(1, (m.lastindex or 0) + 1)}
            # Copiar acción y reemplazar placeholders
            act = json.loads(json.dumps(r["action"]))
            for k, v in list(act.items()):
                if isinstance(v, str):
                    act[k] = v.format(**params)
            return {
                "code": r["code"],
                "category": r["category"],
                "hint": r["hint"].format(**params),
                "params": params,
                "action": act,
                "confidence": 0.9
            }
    return None


def _postprocess_result_html(result: Dict[str, Any]) -> None:
    """Convierte audio_base64 en HTML reproducible automáticamente."""
    if isinstance(result, dict) and "audio_base64" in result and "html_audio" not in result:
        b64 = result["audio_base64"]
        result["html_audio"] = f'<audio src="data:audio/mpeg;base64,{b64}" controls autoplay></audio>'


# ===============================
#  Validación y ejecución de tools (MODO ABIERTO) + Persistencia
# ===============================

def _validate_tool_ast(name: str, code: str) -> None:
    """Validación mínima: nombre válido, tamaño razonable y que exista la función 'name'.
    En modo abierto **NO** se bloquean imports ni dunders.
    """
    try:
        tree = ast.parse(code, mode='exec')
    except SyntaxError as e:
        raise ValueError(f"Error de sintaxis en el código: {e}")
    func_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if name not in func_names:
        raise ValueError(f"Debe definirse una función llamada '{name}'.")


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._dangerous = (os.environ.get("DANGEROUS_TOOLS", "1") != "0")
        # --- Persistencia en disco ---
        self.store_dir = Path(os.environ.get("TOOL_STORE_DIR", ".permanent_tools")).resolve()
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = self.store_dir / "manifest.json"
        self._manifest_data: Dict[str, Any] = self._load_manifest()
        # Cargar tools persistidas en el arranque
        self.load_persisted_tools()

    # --------- Persistencia (manifest & archivos) ---------
    def _load_manifest(self) -> Dict[str, Any]:
        try:
            if self.manifest.exists():
                return json.loads(self.manifest.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"tools": {}}

    def _save_manifest(self) -> None:
        tmp = self.manifest.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.manifest)

    def _tool_path(self, name: str) -> Path:
        safe = re.sub(r"[^a-zA-Z0-9_]+", "_", name).strip("_") or "tool"
        return self.store_dir / f"{safe}.py"

    def _add_callable(self, name: str, code: str) -> None:
        """Registra la función en memoria (sin persistir en disco)."""
        if self._dangerous:
            exec_globals: Dict[str, Any] = {"__builtins__": __builtins__}
        else:
            safe_builtins = {
                'len': len, 'range': range, 'sum': sum,
                'min': min, 'max': max, 'abs': abs,
                'sorted': sorted, 'str': str, 'int': int, 'float': float,
                'bool': bool, 'dict': dict, 'list': list,
            }
            exec_globals = {"__builtins__": safe_builtins}

        # IMPORTANTE: Ejecutar todo en exec_globals para que los imports estén disponibles
        # para la función. No usar exec_locals separado porque los imports no se preservan.
        exec(code, exec_globals, exec_globals)
        fn = exec_globals.get(name)
        if not callable(fn):
            raise ValueError(f"No se encontró una función callable llamada '{name}'.")
        self._tools[name] = fn

    def persist(self, name: str, code: str) -> None:
        path = self._tool_path(name)
        path.write_text(code, encoding="utf-8")
        now = datetime.utcnow().isoformat() + "Z"
        entry = self._manifest_data["tools"].get(name) or {}
        version = int(entry.get("version", 0)) + 1
        self._manifest_data["tools"][name] = {
            "path": str(path),
            "version": version,
            "created_at": entry.get("created_at") or now,
            "updated_at": now
        }
        self._save_manifest()

    def load_persisted_tools(self) -> int:
        loaded = 0
        # 1) Manifest
        for name, meta in list(self._manifest_data.get("tools", {}).items()):
            try:
                p = Path(meta.get("path", ""))
                if p.exists() and name not in self._tools:
                    code = p.read_text(encoding="utf-8")
                    _validate_tool_ast(name, code)
                    self._add_callable(name, code)
                    loaded += 1
            except Exception:
                # Si falla, lo omitimos pero no rompemos el arranque
                continue
        # 2) Exploración de .py en carpeta (por si faltan en manifest)
        for py in self.store_dir.glob("*.py"):
            name = py.stem
            if name in self._tools:
                continue
            try:
                code = py.read_text(encoding="utf-8")
                _validate_tool_ast(name, code)
                self._add_callable(name, code)
                if name not in self._manifest_data.get("tools", {}):
                    now = datetime.utcnow().isoformat() + "Z"
                    self._manifest_data.setdefault("tools", {})[name] = {
                        "path": str(py), "version": 1, "created_at": now, "updated_at": now
                    }
                loaded += 1
            except Exception:
                pass
        if loaded:
            self._save_manifest()
        return loaded

    def register_callable(self, name: str, fn, source: str = "mcp", meta: dict | None = None) -> None:
        """Registra una tool externa (no guarda .py en disco).
        
        Útil para tools de servidores MCP o cualquier callable externo.
        Se registra en el manifest para que aparezca en listados, pero sin archivo .py.
        
        Args:
            name: Nombre de la tool (ej: "server:tool")
            fn: Callable que acepta dict y retorna resultado JSON-serializable
            source: Origen de la tool (default: "mcp")
            meta: Metadatos adicionales opcionales (ej: {"server": "weather"})
        """
        self._tools[name] = fn  # mismo mapa que usan las tools persistentes
        now = datetime.utcnow().isoformat() + "Z"
        entry = {
            "path": None,  # No hay archivo en disco
            "version": 1,
            "created_at": now,
            "updated_at": now,
            "source": source
        }
        if meta:
            entry.update(meta)
        self._manifest_data.setdefault("tools", {})[name] = entry
        self._save_manifest()

    # --------- API pública ---------
    def has(self, name: str) -> bool:
        return name in self._tools

    def add_from_code(self, name: str, code: str):
        _validate_tool_ast(name, code)
        self._add_callable(name, code)
        # Persistir a disco
        self.persist(name, code)

    def call(self, name: str, args: Dict[str, Any]) -> Any:
        if name not in self._tools:
            raise KeyError(f"Herramienta desconocida: {name}")
        try:
            return self._tools[name](args)
        except NameError as e:
            # Error común: import faltante
            error_str = str(e)
            
            # Detectar qué nombre falta y sugerir el import específico
            missing_name = None
            if "'" in error_str:
                missing_name = error_str.split("'")[1]
            
            suggestion = "Probablemente falta un 'import' al inicio del código."
            
            # Sugerencias específicas según el nombre faltante
            import_suggestions = {
                "os": "import os",
                "sys": "import sys",
                "Path": "from pathlib import Path",
                "json": "import json",
                "re": "import re",
                "datetime": "from datetime import datetime",
                "requests": "import requests",
                "subprocess": "import subprocess",
                "BeautifulSoup": "from bs4 import BeautifulSoup",
                "base64": "import base64"
            }
            
            if missing_name and missing_name in import_suggestions:
                suggestion = f"❌ FALTA IMPORT: Agrega '{import_suggestions[missing_name]}' al inicio del código.\n\n💡 El código DEBE comenzar así:\n\n{import_suggestions[missing_name]}\n# ... otros imports si necesitas\n\ndef {name}(args):\n    # tu código..."
            else:
                suggestion += f" Verifica que todos los módulos necesarios estén importados al inicio."
            
            # Verificar si el modo peligroso está activo
            if not self._dangerous:
                suggestion += "\n\n⚠️ ADVERTENCIA: El modo DANGEROUS_TOOLS está desactivado. Esto puede causar problemas con imports."
            
            return {
                "ok": False,
                "error": f"NameError: {error_str}",
                "code": "PY_NAMEERROR_IMPORT",
                "blame": "tool_code",
                "missing_name": missing_name,
                "suggestion": suggestion,
                "traceback": traceback.format_exc(limit=3)
            }
        except ImportError as e:
            module_name = str(e).split("'")[1] if "'" in str(e) else "unknown"
            return {
                "ok": False,
                "error": f"ImportError: {str(e)}",
                "code": "PY_IMPORTERROR",
                "blame": "env",
                "module": module_name,
                "suggestion": f"El módulo '{module_name}' no está instalado. Instálalo con: pip install {module_name}",
                "traceback": traceback.format_exc(limit=3)
            }
        except KeyError as e:
            return {
                "ok": False,
                "error": f"KeyError: {str(e)}",
                "code": "PY_KEYERROR",
                "blame": "input",
                "suggestion": "Falta una clave esperada en el diccionario. Verifica la estructura de datos.",
                "traceback": traceback.format_exc(limit=3)
            }
        except Exception as e:
            return {
                "ok": False,
                "error": f"{type(e).__name__}: {str(e)}",
                "code": f"PY_{type(e).__name__.upper()}",
                "blame": "tool_code",
                "traceback": traceback.format_exc(limit=5)
            }

    def list(self) -> List[str]:
        return sorted(self._tools.keys())


# ===============================
#  Prompts
# ===============================
CODER_SYSTEM = """Eres el *Agente Programador*.
Resuelve la tarea de la forma más simple y confiable posible.

Puedes:
- Responder directamente (type='final'), o
- Crear una herramienta Python y llamarla (type='create_tool'), o
- Llamar una herramienta previamente creada (type='call_tool'), o
- Crear un agente especializado (type='create_agent'), o
- Llamar un agente especializado (type='call_agent').

**DIFERENCIA CRÍTICA ENTRE TOOLS Y AGENTS**:

**TOOLS (create_tool)**:
- Son funciones Python ejecutables
- DEBEN tener código Python válido con `def nombre(args): ...`
- Para tareas computacionales: scraping, cálculos, archivos, APIs
- Ejemplo: scraper, calculadora, lector de CSV

**AGENTS (create_agent)**:
- Son asistentes especializados con prompts personalizados
- NO requieren código Python, solo un system_prompt
- Para tareas de razonamiento, análisis, revisión, generación de contenido
- Ejemplo: analista de datos, revisor de calidad, verificador de hechos

**CUÁNDO USAR CADA UNO**:
- ¿Necesitas EJECUTAR código? → create_tool
- ¿Necesitas un EXPERTO que analice/revise/opine? → create_agent

Reglas de herramienta (MODO ABIERTO):
- **Se permiten `import`**, dunders, red (HTTP), sistema de archivos, uso de `subprocess` (p. ej. `pip`).

**🚨 CRÍTICO - IMPORTS**:
- **LA PRIMERA LÍNEA DEL CÓDIGO DEBE SER UN IMPORT** si usas módulos externos
- Si usas `os` → DEBES poner `import os` en la PRIMERA LÍNEA
- Si usas `Path` → DEBES poner `from pathlib import Path` en la PRIMERA LÍNEA
- Si usas `json` → DEBES poner `import json` en la PRIMERA LÍNEA
- **NUNCA olvides los imports**. El 90% de errores NameError es por imports faltantes.

Ejemplo CORRECTO:
```python
import os
import json

def mi_herramienta(args):
    # ahora puedo usar os y json
    ...
```

Ejemplo INCORRECTO (causa NameError):
```python
def mi_herramienta(args):
    os.path.exists(...)  # ❌ ERROR: 'os' is not defined
```

Otras reglas:
- La función debe llamarse exactamente como 'tool.name'.
- Firma: `def <name>(args: dict) -> (dict|list|str|int|float|bool)`.
- Devuelve **solo valores JSON-serializables**. Si lees binarios, devuélvelos codificados (p. ej. base64) o a disco y retorna la ruta.
- Si haces scraping, intenta respetar robots.txt y Términos del sitio.
- **MANEJO DE ERRORES**: Siempre usa try/except para capturar excepciones y devuelve dict con 'ok' y 'error' cuando falle.

**CORRECCIÓN DE ERRORES**:
- Si una herramienta falló, DEBES corregirla creando una nueva versión con el MISMO nombre.
- Lee cuidadosamente el error reportado y corrígelo específicamente.
- Si falta un import, agrégalo. Si hay un bug lógico, corrígelo.
- NO ignores los errores previos, apréndelos y corrígelos.

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
    "code": "def nombre_funcion(args):\n    ...\n    return {...}"
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

(4) Crear agente especializado:
{
  "type": "create_agent",
  "message": "por qué se necesita este agente",
  "agent": {
    "name": "nombre_agente",
    "role": "Rol descriptivo del agente",
    "system_prompt": "Eres un agente especializado en... Tu tarea es...",
    "capabilities": ["capacidad1", "capacidad2"]
  },
  "call": {
    "agent_name": "nombre_agente",
    "task": "tarea específica para el agente"
  }
}

(5) Llamar agente existente:
{
  "type": "call_agent",
  "message": "qué va a hacer el agente",
  "call": {
    "agent_name": "nombre_agente",
    "task": "tarea específica"
  }
}

**EJEMPLOS CLAROS**:

✅ CREAR AGENTE para:
- "Verifica si esta información es factualmente correcta"
- "Revisa este texto y mejora su calidad"
- "Analiza estos datos y genera insights de negocio"
- "Diseña una estrategia de marketing"

✅ CREAR TOOL para:
- "Descarga el contenido de esta URL"
- "Calcula el factorial de un número"
- "Lee este archivo CSV y extrae columnas"
- "Hace una petición a la API de clima"

Los agentes creados persisten y pueden ser reutilizados.
"""


SUPERVISOR_SYSTEM = """Eres el *Supervisor*.
Evalúa si la salida satisface la tarea. Devuelve SOLO JSON:
{
  "route": "end" | "coder",
  "reason": "breve justificación",
  "tips": ["consejo 1", "consejo 2", "consejo 3"]  // 3–6 sugerencias accionables para el próximo paso
}

Criterio:
- Si hay una respuesta clara/útil -> end.
- Si falta completar/mejorar -> coder.
- **Si hay un ERROR de ejecución -> coder con tips específicos de corrección**.

Guía para 'tips':
- Sé específico y verificable (p.ej., "agrega pruebas para X", "maneja error Y", "cubre caso límite Z").
- **CRÍTICO para errores**: Si ves un error como "name 'X' is not defined", el primer tip debe ser "Agrega 'import X' al inicio del código".
- Si hay un error de sintaxis, indica exactamente qué corregir.
- Si falta manejo de excepciones, indica qué excepciones capturar.
- Incluye, cuando aplique: siguiente acción, cómo validarla, y un criterio de salida.
- Enfoca en brechas observables: imports faltantes, pruebas, manejo de errores, casos límite, rendimiento, seguridad, UX, fuentes/citas, estructura del código.
- **Prioriza la corrección de errores sobre nuevas features**.
"""


# ===============================
#  Agentes
# ===============================
class CoderAgent:
    def __init__(self, llm: CloudflareLLMClient, model: Optional[str] = None):
        self.llm = llm
        self.model = model or os.environ.get('CF_MODEL', '@cf/openai/gpt-oss-120b')

    def step(self, task: str, transcript: List[Dict[str, str]]) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": CODER_SYSTEM},
            *transcript,
            {"role": "user", "content": f"Tarea: {task}\n\nResponde SOLO con JSON."},
        ]
        raw = self.llm.chat(messages, model=self.model, temperature=0.2, max_tokens=1500)
        return extract_json(raw)


class Supervisor:
    def __init__(self, llm: CloudflareLLMClient, model: Optional[str] = None):
        self.llm = llm
        self.model = model or os.environ.get('CF_MODEL', '@cf/openai/gpt-oss-120b')

    def decide(self, task: str, transcript: List[Dict[str, str]]) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": SUPERVISOR_SYSTEM},
            *transcript,
            {"role": "user", "content": f"Tarea original: {task}\n\n¿Terminar (end) o derivar (coder)? Devuelve SOLO JSON."},
        ]
        raw = self.llm.chat(messages, model=self.model, temperature=0.0, max_tokens=400)
        return extract_json(raw)


# ===============================
#  Orquestador
# ===============================
class MiniAgentSystem:
    def __init__(self, llm: CloudflareLLMClient, recorder: Optional[Recorder] = None, session_manager: Optional[SessionManager] = None, agent_registry: Optional[AgentRegistry] = None):
        self.llm = llm
        self.coder = CoderAgent(llm)
        self.supervisor = Supervisor(llm)
        self.tools = ToolRegistry()  # Carga persistentes en el __init__
        self.agents = agent_registry or AgentRegistry(llm)  # Registro de agentes dinámicos
        self.recorder = recorder
        self.session_manager = session_manager or SessionManager()
        self.current_session_id: Optional[str] = None
        self.tools_used_in_session: List[str] = []
        self.agents_used_in_session: List[str] = []
        # Telemetría y preferencias del usuario
        self.session_custom_data: Dict[str, Any] = {
            "tool_stats": {},
            "agent_stats": {},
            "user_prefs": {}
        }
        
        # --------- Autoconexión de servidores MCP ---------
        self.mcp_bridge = None
        self.mcp_stats = None
        cfg = os.environ.get("MCP_STDIO")
        if cfg:
            try:
                from coreee.mcp_bridge import connect_mcp_servers_from_env
                
                # Ejecutar conexión async de forma síncrona
                loop = asyncio.get_event_loop()
                self.mcp_stats = loop.run_until_complete(
                    connect_mcp_servers_from_env(self.tools, env_var="MCP_STDIO")
                )
                
                # Registrar evento de conexión en recorder si está disponible
                if self.recorder and self.mcp_stats:
                    if self.mcp_stats["servers_connected"] > 0:
                        self.recorder.emit(
                            turn=0, 
                            role="system", 
                            etype="mcp_connected",
                            summary=f"MCP: {self.mcp_stats['servers_connected']} servidores, {self.mcp_stats['total_tools']} tools",
                            data=self.mcp_stats
                        )
                    if self.mcp_stats.get("errors"):
                        for err in self.mcp_stats["errors"]:
                            self.recorder.emit(
                                turn=0,
                                role="system",
                                etype="mcp_error",
                                summary=f"Error en servidor '{err['server']}'",
                                data=err
                            )
            except ImportError:
                # El paquete 'mcp' no está instalado
                if self.recorder:
                    self.recorder.emit(
                        turn=0,
                        role="system",
                        etype="mcp_unavailable",
                        summary="Paquete 'mcp' no instalado. Ejecuta: pip install mcp",
                        data={"env_var": "MCP_STDIO", "value": cfg[:100]}
                    )
            except Exception as e:
                # Error genérico conectando MCP
                if self.recorder:
                    self.recorder.emit(
                        turn=0, 
                        role="system", 
                        etype="mcp_error",
                        summary=f"Error autoconectando MCP: {str(e)}",
                        data={"error": str(e), "traceback": traceback.format_exc()}
                    )

    def _append(self, transcript: List[Dict[str, str]], role: str, content: str) -> None:
        transcript.append({"role": role, "content": content})

    def _print_turn(self, msg: Dict[str, str]) -> None:
        role = msg.get("role", "").upper()
        content = msg.get("content", "")
        print(f"\n[{role}] {content}")

    def _save_session_snapshot(self, transcript, task, turn, status="active"):
        """Fusiona y persiste custom_data con telemetría."""
        custom = deepcopy(self.session_custom_data)
        custom.setdefault("agents_used", self.agents_used_in_session)
        self.session_manager.save_session(
            session_id=self.current_session_id,
            transcript=transcript,
            metadata={"task": task, "total_turns": turn, "model": self.coder.model},
            tools_used=self.tools_used_in_session,
            custom_data=custom,
            status=status
        )

    def _update_tool_stats(self, tool_name: str, ok: bool, latency_ms: float, args: dict, result: Any, contributed=False):
        """Actualiza estadísticas y score de una herramienta."""
        stats = self.session_custom_data.setdefault("tool_stats", {}).setdefault(tool_name, {
            "calls": 0, "ok": 0, "errors": 0, "avg_latency_ms": None, "last_error": None,
            "last_args_sample": None, "score": 0.0, "last_ok_at": None
        })
        stats["calls"] += 1
        if ok:
            stats["ok"] += 1
            stats["last_ok_at"] = datetime.utcnow().isoformat() + "Z"
        else:
            stats["errors"] += 1
            err = None
            if isinstance(result, dict):
                err = result.get("code") or result.get("error")
            stats["last_error"] = str(err)[:300] if err else "unknown"

        # Latencia exponencial suavizada
        if stats["avg_latency_ms"] is None:
            stats["avg_latency_ms"] = latency_ms
        else:
            stats["avg_latency_ms"] = 0.8 * stats["avg_latency_ms"] + 0.2 * latency_ms

        # Samplear args (sanitizado básico)
        sample = {k: (v if isinstance(v, (int, float, bool)) else str(v)[:120]) for k, v in (args or {}).items()}
        stats["last_args_sample"] = sample

        # Score: éxito (peso 1.0), penalización por error (0.6), latencia (suave), bonus si contribuye a éxito final
        ok_rate = stats["ok"] / max(1, stats["calls"])
        err_rate = stats["errors"] / max(1, stats["calls"])
        latency_pen = 0.0 if stats["avg_latency_ms"] is None else min(stats["avg_latency_ms"] / 3000.0, 0.4)
        bonus = 0.2 if contributed else 0.0
        stats["score"] = round(max(0.0, ok_rate - 0.6 * err_rate - latency_pen + bonus), 4)

    def _update_user_prefs(self, tool_name: str, args: dict, ok: bool):
        """Captura preferencias del usuario basadas en éxito de herramientas."""
        prefs = self.session_custom_data.setdefault("user_prefs", {})
        # Ejemplo: preferencia de voz si TTS
        if ok and "voice_id" in (args or {}) and "tts" in tool_name.lower():
            prefs["tts_preferred_voice_id"] = args["voice_id"]

    def _summarize_top_tools(self) -> str:
        """Genera resumen de top 5 herramientas por score."""
        stats = self.session_custom_data.get("tool_stats", {})
        if not stats:
            return "No hay métricas de herramientas aún."
        ordered = sorted(stats.items(), key=lambda kv: kv[1].get("score", 0.0), reverse=True)[:5]
        lines = []
        for name, s in ordered:
            lines.append(f"- {name}: score={s.get('score',0):.3f}, ok={s['ok']}/{s['calls']}, avg_ms={int(s.get('avg_latency_ms') or 0)}")
        return "\n".join(lines)

    def _inject_prefs_for_coder(self, transcript: List[Dict[str, str]]):
        """Inyecta contexto de preferencias y ranking al Coder."""
        summary = self._summarize_top_tools()
        prefs = self.session_custom_data.get("user_prefs", {})
        blob = {
            "top_tools": summary,
            "user_prefs": prefs
        }
        # Nota: lo metemos como "contexto" legible para el Coder
        self._append(transcript, 'assistant', f"[Contexto] Preferencias y ranking de tools:\n```json\n{json.dumps(blob, ensure_ascii=False, indent=2)}\n```")

    def run(
        self,
        task: str,
        max_turns: int = 5,
        stream: bool = False,
        save_transcript_path: Optional[str] = None,
        session_id: Optional[str] = None,
        resume_session: bool = False,
    ) -> Dict[str, Any]:
        # Cargar sesión anterior si se solicita
        if resume_session and session_id:
            loaded = self.session_manager.load_session(session_id)
            if loaded:
                transcript = loaded.transcript.copy()
                self.current_session_id = session_id
                # Cambiar AgentRegistry a la sesión cargada
                self.agents.switch_session(session_id)
                self.tools_used_in_session = loaded.tools_used.copy()
                # Hidratar telemetría y preferencias desde sesión previa
                if loaded.custom_data and isinstance(loaded.custom_data, dict):
                    self.session_custom_data = deepcopy(loaded.custom_data)
                    if "tool_stats" not in self.session_custom_data:
                        self.session_custom_data["tool_stats"] = {}
                    if "agent_stats" not in self.session_custom_data:
                        self.session_custom_data["agent_stats"] = {}
                    if "user_prefs" not in self.session_custom_data:
                        self.session_custom_data["user_prefs"] = {}
                if stream:
                    print(f"[SISTEMA] Reanudando sesión '{session_id}' con {len(transcript)} mensajes previos.")
                if self.recorder:
                    self.recorder.emit(turn=0, role="system", etype="session_resumed", summary=f"session_id={session_id}", data={"transcript_length": len(transcript)})
            else:
                if stream:
                    print(f"[SISTEMA] No se encontró la sesión '{session_id}'. Iniciando nueva sesión.")
                transcript = []
        else:
            transcript = []
        
        # Crear o actualizar sesión
        if session_id:
            self.current_session_id = session_id
            # Cambiar AgentRegistry a esta sesión
            self.agents.switch_session(session_id)
        
        turn = len(transcript)  # Continuar desde el último turno
        if self.recorder and not resume_session:
            # Emitir mensaje del usuario
            self.recorder.emit(turn=turn, role="user", etype="user_message", summary=task[:200], data={"content": task, "message_type": "task"})
            # Emitir inicio de ejecución
            self.recorder.emit(turn=turn, role="system", etype="run_started", summary=f"task={task}", data={"max_turns": max_turns})

        for _ in range(max_turns):
            turn += 1
            try:
                # Inyectar contexto de telemetría y preferencias para el Coder
                if self.session_custom_data.get("tool_stats"):
                    self._inject_prefs_for_coder(transcript)
                
                if self.recorder:
                    self.recorder.emit(turn=turn, role="coder", etype="coder_step_request", summary="consulta al Coder")
                coder_out = self.coder.step(task, transcript)
                if self.recorder:
                    self.recorder.emit(turn=turn, role="coder", etype="coder_step_parsed", data={"keys": list(coder_out.keys())}, summary=f"type={coder_out.get('type')}")
            except Exception as e:
                if self.recorder:
                    self.recorder.emit(turn=turn, role="coder", etype="coder_parse_error", summary=str(e))
                self._append(transcript, 'assistant', f"[Coder] Error parseando salida del LLM: {e}")
                if stream: self._print_turn(transcript[-1])
                # Pedir nuevo intento
                self._append(transcript, 'user', '[Supervisor] Reintenta con JSON válido y conciso.')
                if stream: self._print_turn(transcript[-1])
                continue

            ctype = (coder_out.get('type') or '').lower()

            if ctype == 'final':
                answer = str(coder_out.get('answer', ''))
                message = str(coder_out.get('message', ''))
                self._append(transcript, 'assistant', f"[Coder] {message}\n\nPropuesta de respuesta:\n{answer}")
                if self.recorder:
                    # Emitir mensaje del Coder
                    self.recorder.emit(turn=turn, role="coder", etype="coder_message", summary=message[:200], data={"content": message, "action": "final_answer"})
                    # Emitir propuesta final
                    path = self.recorder.write_blob(f"final/turn_{turn:03d}_answer.txt", answer)
                    self.recorder.emit(turn=turn, role="coder", etype="coder_final_proposal", summary=message, data={"answer_path": path, "answer": answer})
                if stream: self._print_turn(transcript[-1])

            elif ctype in ('create_tool', 'call_tool'):
                call = coder_out.get('call', {}) or {}
                msg = str(coder_out.get('message', ''))
                name = str(call.get('name', ''))
                args = call.get('args', {}) or {}

                if ctype == 'create_tool':
                    tool = coder_out.get('tool', {}) or {}
                    tname = tool.get('name') or name
                    code = str(tool.get('code', ''))
                    
                    # Detectar si es creación nueva o actualización
                    is_update = self.tools.has(tname)
                    action = "actualizada" if is_update else "creada"
                    event_type = "tool_update" if is_update else "tool_create"
                    
                    if self.recorder:
                        # Emitir mensaje del Coder sobre la creación
                        self.recorder.emit(turn=turn, role="coder", etype="coder_message", summary=msg[:200], data={"content": msg, "action": "creating_tool", "tool_name": tname})
                        # Emitir creación de herramienta con código
                        code_path = self.recorder.write_blob(f"tools_session/turn_{turn:03d}_{tname}.py", code)
                        self.recorder.emit(turn=turn, role="coder", etype=event_type, summary=f"def {tname}(args) - {action}", data={"code_path": code_path, "chars": len(code), "is_update": is_update, "tool_name": tname, "code": code})
                    
                    # Registrar en memoria y **persistir** (permite sobrescritura)
                    try:
                        self.tools.add_from_code(tname, code)
                    except ValueError as e:
                        # Error de validación - probablemente confusión entre tool y agent
                        error_hint = ""
                        if "Debe definirse una función" in str(e):
                            error_hint = "\n\n💡 HINT: Si no necesitas ejecutar código Python, usa 'create_agent' en lugar de 'create_tool'. Los agentes son para razonamiento/análisis, las tools para ejecución de código."
                        self._append(transcript, 'assistant', f"[Coder] Error al crear herramienta '{tname}': {e}{error_hint}")
                        if stream: self._print_turn(transcript[-1])
                        continue
                    except Exception as e:
                        self._append(transcript, 'assistant', f"[Coder] Error inesperado al crear herramienta '{tname}': {e}")
                        if stream: self._print_turn(transcript[-1])
                        continue
                    
                    if self.recorder:
                        self.recorder.emit(turn=turn, role="coder", etype="tool_registered", data={"name": tname, "persistent_dir": str(self.tools.store_dir), "action": action})
                    
                    # Mostrar mensaje informativo si es actualización
                    if is_update and stream:
                        print(f"\n[⟳ HERRAMIENTA ACTUALIZADA] {tname} ha sido corregida/mejorada.")
                    
                    name = tname

                # Ejecutar herramienta
                if self.recorder:
                    self.recorder.emit(turn=turn, role="tool", etype="tool_call", summary=f"{name}(args)", data={"tool_name": name, "args": args})
                
                # Medición de latencia
                t0 = perf_counter()
                result = self.tools.call(name, args)
                lat_ms = (perf_counter() - t0) * 1000.0
                
                # Rastrear herramientas usadas
                if name not in self.tools_used_in_session:
                    self.tools_used_in_session.append(name)
                
                # Post-procesamiento automático: audio_base64 → HTML
                if isinstance(result, dict):
                    _postprocess_result_html(result)
                
                # Normalización + diagnóstico
                diag = None
                if isinstance(result, dict) and (result.get("ok") is False or result.get("error")):
                    err_text = result.get("error") or json.dumps(result)[:800]
                    diag = diagnose(err_text)
                    if diag:
                        result["diagnostic"] = diag
                        if self.recorder:
                            self.recorder.emit(turn=turn, role="assistant",
                                             etype="diagnostic", summary=diag["code"], data=diag)
                
                # Actualizar métricas y preferencias
                ok_flag = True
                if isinstance(result, dict) and (result.get("ok") is False or result.get("error")):
                    ok_flag = False
                self._update_tool_stats(name, ok=ok_flag, latency_ms=lat_ms, args=args, result=result)
                self._update_user_prefs(name, args, ok=ok_flag)
                
                # Registrar evento de scoring en timeline
                if self.recorder:
                    tool_score = self.session_custom_data["tool_stats"][name]["score"]
                    self.recorder.emit(turn=turn, role="system", etype="tool_scored",
                                     summary=f"{name} score={tool_score}",
                                     data={"name": name, "stats": self.session_custom_data["tool_stats"][name]})
                
                # Detectar si hay error en el resultado
                error_msg = ""
                if isinstance(result, dict):
                    if result.get("ok") is False:
                        error_detail = result.get('error', 'desconocido')
                        suggestion = result.get('suggestion', '')
                        traceback_info = result.get('traceback', 'N/A')
                        error_msg = f"\n\n⚠️ ERROR EN HERRAMIENTA: {error_detail}"
                        if suggestion:
                            error_msg += f"\n💡 Sugerencia: {suggestion}"
                        if diag:
                            error_msg += f"\n\n🔍 DIAGNÓSTICO [{diag['code']}]: {diag['hint']}"
                        error_msg += f"\nTraceback: {traceback_info}"
                    elif "error" in result and result["error"]:
                        error_msg = f"\n\n⚠️ ERROR EN HERRAMIENTA: {result['error']}"
                
                # Preparar resultado para transcript (resumir si es grande, incluir HTML si existe)
                result_preview = result
                if isinstance(result, dict) and result.get("html_audio"):
                    result_preview = {"ok": True, "audio_generado": True, "html": result["html_audio"]}
                elif isinstance(result, str) and len(result) > 700:
                    result_preview = result[:700] + "..."
                elif isinstance(result, dict):
                    result_str = json.dumps(result, ensure_ascii=False)
                    if len(result_str) > 700:
                        result_preview = result_str[:700] + "..."
                
                self._append(
                    transcript,
                    'assistant',
                    f"[Coder] {msg}\n\nHerramienta usada: {name}\nArgs: {args}\nResultado: {result_preview}{error_msg}"
                )
                if self.recorder:
                    if isinstance(result, dict) and result.get("ok") is False:
                        self.recorder.emit(turn=turn, role="tool", etype="tool_result_error", data={"tool_name": name, "name": name, "error": result.get("error"), "traceback": result.get("traceback"), "code": result.get("code")})
                    else:
                        self.recorder.emit(turn=turn, role="tool", etype="tool_result_ok", data={"tool_name": name, "name": name, "result": result_preview})
                if stream: self._print_turn(transcript[-1])

            elif ctype in ('create_agent', 'call_agent'):
                msg = str(coder_out.get('message', ''))
                
                if ctype == 'create_agent':
                    # Crear nuevo agente
                    agent_def = coder_out.get('agent', {}) or {}
                    agent_name = agent_def.get('name', '')
                    agent_role = agent_def.get('role', '')
                    system_prompt = agent_def.get('system_prompt', '')
                    capabilities = agent_def.get('capabilities', [])
                    
                    if not agent_name or not system_prompt:
                        self._append(transcript, 'assistant', f"[Coder] Error: Falta 'name' o 'system_prompt' para crear el agente.")
                        if stream: self._print_turn(transcript[-1])
                        continue
                    
                    # Detectar si es actualización
                    is_update = self.agents.has_agent(agent_name)
                    action = "actualizado" if is_update else "creado"
                    
                    # Crear/actualizar agente
                    try:
                        agent = self.agents.create_agent(
                            name=agent_name,
                            role=agent_role,
                            system_prompt=system_prompt,
                            capabilities=capabilities,
                            created_by="coder"
                        )
                        
                        if self.recorder:
                            self.recorder.emit(
                                turn=turn,
                                role="agent",
                                etype="agent_created" if not is_update else "agent_updated",
                                summary=f"Agente '{agent_name}' {action}",
                                data={
                                    "name": agent_name,
                                    "role": agent_role,
                                    "capabilities": capabilities,
                                    "is_update": is_update
                                }
                            )
                        
                        if is_update and stream:
                            print(f"\n[⟳ AGENTE ACTUALIZADO] {agent_name} ({agent_role})")
                        elif stream:
                            print(f"\n[✨ AGENTE CREADO] {agent_name} ({agent_role})")
                        
                        # Registrar agente usado
                        if agent_name not in self.agents_used_in_session:
                            self.agents_used_in_session.append(agent_name)
                        
                        self._append(
                            transcript,
                            'assistant',
                            f"[Coder] {msg}\n\nAgente {action}: {agent_name}\nRol: {agent_role}\nCapacidades: {', '.join(capabilities)}"
                        )
                        if stream: self._print_turn(transcript[-1])
                        
                    except Exception as e:
                        self._append(transcript, 'assistant', f"[Coder] Error creando agente: {e}")
                        if stream: self._print_turn(transcript[-1])
                        continue
                
                # Llamar al agente (ya sea recién creado o existente)
                call = coder_out.get('call', {}) or {}
                agent_name = call.get('agent_name', '')
                agent_task = call.get('task', '')
                
                if agent_name and agent_task:
                    if self.recorder:
                        self.recorder.emit(
                            turn=turn,
                            role="agent",
                            etype="agent_call",
                            summary=f"Llamando a agente '{agent_name}'",
                            data={"agent_name": agent_name, "task": agent_task}
                        )
                    
                    # Llamar al agente con contexto
                    result = self.agents.call_agent(agent_name, agent_task, transcript)
                    
                    # Registrar uso del agente
                    if agent_name not in self.agents_used_in_session:
                        self.agents_used_in_session.append(agent_name)
                    
                    if result.get('ok'):
                        agent_response = result.get('response', '')
                        agent_role = result.get('agent_role', '')
                        system_prompt_preview = result.get('system_prompt_preview', '')
                        
                        # Mostrar info del agente especializado
                        agent_info = f"[Agente Especializado: {agent_name}] ({agent_role})"
                        if system_prompt_preview:
                            agent_info += f"\n🧠 Expertise: {system_prompt_preview}..."
                        agent_info += f"\n\n📋 Tarea asignada: {agent_task}\n\n💬 Respuesta del agente:\n{agent_response}"
                        
                        self._append(
                            transcript,
                            'assistant',
                            agent_info
                        )
                        
                        if self.recorder:
                            self.recorder.emit(
                                turn=turn,
                                role="agent",
                                etype="agent_response_ok",
                                data={"agent_name": agent_name, "response_length": len(agent_response)}
                            )
                    else:
                        error = result.get('error', 'Error desconocido')
                        self._append(
                            transcript,
                            'assistant',
                            f"[Coder] Error al llamar agente '{agent_name}': {error}"
                        )
                        
                        if self.recorder:
                            self.recorder.emit(
                                turn=turn,
                                role="agent",
                                etype="agent_response_error",
                                data={"agent_name": agent_name, "error": error}
                            )
                    
                    if stream: self._print_turn(transcript[-1])

            else:
                self._append(transcript, 'assistant', f"[Coder] Tipo desconocido: {ctype}. Solicito nuevo intento.")
                if stream: self._print_turn(transcript[-1])

            # Decisión del supervisor
            try:
                decision = self.supervisor.decide(task, transcript)
                route = (decision.get('route') or '').lower()
                if self.recorder:
                    self.recorder.emit(turn=turn, role="supervisor", etype="supervisor_decision", data=decision, summary=f"route={route}")
            except Exception as e:
                route = 'coder'
                decision = {'route': 'coder', 'reason': f'Error del supervisor: {e}', 'tips': ['Revisa el error y continúa.']}
                self._append(transcript, 'assistant', f"[Supervisor] Error interpretando decisión: {e}. Continuar con coder.")
                if stream: self._print_turn(transcript[-1])

            if route == 'end':
                last = next((m for m in reversed(transcript) if m['role'] == 'assistant'), None)
                final = last['content'] if last else 'Tarea finalizada.'
                
                # Bonus para la última tool que contribuyó al éxito
                if self.tools_used_in_session:
                    last_tool = self.tools_used_in_session[-1]
                    self._update_tool_stats(last_tool, ok=True, latency_ms=0, args={}, result={}, contributed=True)
                
                # Guardar sesión persistente con telemetría
                if self.current_session_id:
                    self._save_session_snapshot(transcript, task, turn, status="completed")
                # Guardar transcript si se pidió
                if save_transcript_path:
                    try:
                        with open(save_transcript_path, "w", encoding="utf-8") as f:
                            import json as _json
                            _json.dump(transcript, f, ensure_ascii=False, indent=2)
                    except Exception as _:
                        pass
                if self.recorder:
                    self.recorder.emit(turn=turn, role="system", etype="run_finished", summary="end")
                return {"final": final, "transcript": transcript, "session_id": self.current_session_id}

            # Feedback del supervisor con tips
            reason = decision.get('reason', 'Continúa trabajando')
            tips = decision.get('tips', [])
            if tips:
                tips_text = "\n".join(f"  {i+1}. {tip}" for i, tip in enumerate(tips[:6]))
                feedback = f"[Supervisor] {reason}\n\nAcciones requeridas:\n{tips_text}\n\n🔄 Por favor, corrige los errores y vuelve a intentar."
            else:
                feedback = f"[Supervisor] {reason}\n\n🔄 Continúa mejorando la solución."
            self._append(transcript, 'user', feedback)
            if self.recorder:
                self.recorder.emit(turn=turn, role="supervisor", etype="iteration_continue")
            if stream: self._print_turn(transcript[-1])
            
            # Guardar progreso de sesión cada turno
            if self.current_session_id:
                self._save_session_snapshot(transcript, task, turn, status="active")

        last = next((m for m in reversed(transcript) if m['role'] == 'assistant'), None)
        final = last['content'] if last else 'No se pudo completar en los turnos permitidos.'
        # Guardar sesión (estado: activa porque no se completó)
        if self.current_session_id:
            self._save_session_snapshot(transcript, task, turn, status="active")
        if save_transcript_path:
            try:
                with open(save_transcript_path, "w", encoding="utf-8") as f:
                    import json as _json
                    _json.dump(transcript, f, ensure_ascii=False, indent=2)
            except Exception as _:
                pass
        return {"final": final, "transcript": transcript, "session_id": self.current_session_id}


# ===============================
#  Ejecución directa
# ===============================
if __name__ == '__main__':
    llm = CloudflareLLMClient()
    # --- CLI extendido ---
    parser = argparse.ArgumentParser(description='Mini sistema de agentes (supervisor + coder) con tools persistentes.')
    parser.add_argument('-q', '--question', '--task', dest='task', help='Tarea o pregunta a resolver.')
    parser.add_argument('-m', '--max-turns', dest='max_turns', type=int, default=10, help='Máximo de turnos (default: 10 para permitir correcciones).')
    parser.add_argument('--log-dir', dest='log_dir', default='.runs', help='Directorio base para logs/timeline.')
    parser.add_argument('--tools-list', action='store_true', help='Listar tools persistentes y salir.')
    parser.add_argument('--tools-dir', dest='tools_dir', default=os.environ.get('TOOL_STORE_DIR', '.permanent_tools'), help='Directorio de tools persistentes.')
    # Argumentos para agentes
    parser.add_argument('--agents-list', action='store_true', help='Listar agentes dinámicos de la sesión actual (o global si no hay session-id).')
    parser.add_argument('--agents-all-sessions', action='store_true', help='Listar agentes de TODAS las sesiones.')
    parser.add_argument('--agent-info', dest='agent_info', help='Mostrar información detallada de un agente específico.')
    parser.add_argument('--agents-dir', dest='agents_dir', default='.agents', help='Directorio base de agentes dinámicos.')
    # Nuevos argumentos para sesiones
    parser.add_argument('--session-id', dest='session_id', help='ID de la sesión (auto-generado si no se especifica).')
    parser.add_argument('--resume', dest='resume_session', action='store_true', help='Reanudar sesión anterior especificada con --session-id.')
    parser.add_argument('--sessions-list', dest='sessions_list', action='store_true', help='Listar sesiones guardadas y salir.')
    parser.add_argument('--sessions-dir', dest='sessions_dir', default='.sessions', help='Directorio de sesiones persistentes.')
    parser.add_argument('--delete-session', dest='delete_session', help='Eliminar una sesión por ID.')
    args = parser.parse_args()

    # Definir carpeta de sesión
    session_dir = Path(args.log_dir) / datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    # Usar EnhancedRecorder para emitir al EventBus (dashboard en tiempo real)
    session_id = args.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    recorder = EnhancedRecorder(str(session_dir), session_id=session_id)

    # Respetar --tools-dir
    os.environ['TOOL_STORE_DIR'] = args.tools_dir
    
    # Crear gestor de sesiones
    session_mgr = SessionManager(args.sessions_dir)
    
    # Crear registro de agentes (con session_id para aislamiento)
    agent_registry = AgentRegistry(llm, args.agents_dir, session_id=session_id)

    system = MiniAgentSystem(llm, recorder=recorder, session_manager=session_mgr, agent_registry=agent_registry)

    # Comando: listar tools
    if args.tools_list:
        print("Tools persistentes en", system.tools.store_dir)
        for name in system.tools.list():
            print(" -", name)
        raise SystemExit(0)
    
    # Comando: listar agentes de todas las sesiones
    if args.agents_all_sessions:
        print(f"Agentes dinámicos por sesión (directorio base: {system.agents.agents_base_dir}):")
        sessions = system.agents.list_all_sessions()
        if not sessions:
            print("  (ningún agente creado aún en ninguna sesión)")
        else:
            counts = system.agents.count_agents_by_session()
            for session in sessions:
                count = counts.get(session, 0)
                print(f"\n📁 Sesión: {session} ({count} agente(s))")
                # Cambiar temporalmente a esa sesión para listar
                temp_registry = AgentRegistry(llm, args.agents_dir, session_id=session)
                agents = temp_registry.list_agents()
                if agents:
                    print(f"  {'Nombre':18s} {'Rol':28s} {'Capacidades':38s}")
                    print("  " + "=" * 90)
                    for agent in agents:
                        caps = ', '.join(agent['capabilities'][:2])
                        if len(agent['capabilities']) > 2:
                            caps += '...'
                        print(f"  {agent['name']:18s} {agent['role']:28s} {caps:38s}")
            print(f"\n📊 Total: {len(sessions)} sesión(es) con agentes")
        raise SystemExit(0)
    
    # Comando: listar agentes de la sesión actual
    if args.agents_list:
        current_session = args.session_id or "global"
        print(f"🤖 Agentes dinámicos de la sesión: {current_session}")
        print(f"Directorio: {system.agents.agents_dir}\n")
        agents = system.agents.list_agents()
        if not agents:
            print("  (ningún agente creado aún en esta sesión)")
            # Mostrar hint sobre otras sesiones
            all_sessions = system.agents.list_all_sessions()
            if len(all_sessions) > 1:
                print(f"\n💡 Hay agentes en otras sesiones: {', '.join([s for s in all_sessions if s != current_session])}")
                print("   Usa --agents-all-sessions para verlos todos")
        else:
            print(f"{'Nombre':20s} {'Rol':30s} {'Capacidades':40s} {'Creado por':15s}")
            print("=" * 110)
            for agent in agents:
                caps = ', '.join(agent['capabilities'][:3])  # Primeras 3 capacidades
                if len(agent['capabilities']) > 3:
                    caps += '...'
                print(f"{agent['name']:20s} {agent['role']:30s} {caps:40s} {agent['created_by']:15s}")
            print(f"\nTotal: {len(agents)} agente(s) en esta sesión")
            print(f"\n💡 Tips:")
            print(f"  - Ver detalles: --agent-info NOMBRE --session-id {current_session}")
            print(f"  - Ver todas las sesiones: --agents-all-sessions")
        raise SystemExit(0)
    
    # Comando: info de agente
    if args.agent_info:
        agent_name = args.agent_info
        agent = system.agents.get_agent(agent_name)
        if not agent:
            print(f"❌ Agente '{agent_name}' no encontrado.")
            print(f"\nAgentes disponibles: {', '.join(system.agents.list_agents()) if system.agents.list_agents() else 'ninguno'}")
        else:
            print(f"\n{'='*80}")
            print(f"🤖 AGENTE: {agent.name}")
            print(f"{'='*80}")
            print(f"\n🎭 Rol: {agent.role}")
            print(f"\n📅 Creado: {agent.definition.created_at}")
            print(f"👤 Creado por: {agent.definition.created_by}")
            print(f"\n🧠 System Prompt:")
            print(f"  {agent.definition.system_prompt}")
            print(f"\n✨ Capacidades:")
            for cap in agent.definition.capabilities:
                print(f"  • {cap}")
            print(f"\n⚙️ Configuración:")
            print(f"  Temperature: {agent.definition.temperature}")
            print(f"  Max Tokens: {agent.definition.max_tokens}")
            print(f"  Model: {agent.definition.model or 'default'}")
            print(f"\n{'='*80}\n")
        raise SystemExit(0)
    
    # Comando: listar sesiones
    if args.sessions_list:
        print(f"Sesiones guardadas en {session_mgr.sessions_dir}:")
        sessions = session_mgr.list_sessions()
        if not sessions:
            print("  (ninguna sesión guardada)")
        else:
            for s in sessions:
                status_icon = "✓" if s["status"] == "completed" else "○"
                print(f"  {status_icon} {s['session_id']:30s} | {s.get('task', '')[:50]:50s} | {s['status']:10s} | {s.get('updated_at', '')}")
        raise SystemExit(0)
    
    # Comando: eliminar sesión
    if args.delete_session:
        if session_mgr.delete_session(args.delete_session):
            print(f"Sesión '{args.delete_session}' eliminada.")
        else:
            print(f"No se encontró la sesión '{args.delete_session}'.")
        raise SystemExit(0)

    # Generar o usar session_id
    if args.session_id:
        session_id = args.session_id
    else:
        # Auto-generar ID basado en timestamp
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    tarea = (
        args.task
        or os.environ.get('AGENT_TASK')
        or input('Escribe tu pregunta/tarea: ').strip()
        or 'Escribe una tool que scrappee 10 titulares de https://www.latercera.com/ y devuélvelos en lista.'
    )

    # Guardamos también el transcript en la sesión
    resultado = system.run(
        tarea, 
        max_turns=args.max_turns, 
        save_transcript_path=str(session_dir / 'transcript.json'),
        session_id=session_id,
        resume_session=args.resume_session
    )

    # Compilamos timeline legible
    md_path = recorder.save_markdown(str(session_dir / 'timeline.md'))
    html_path = recorder.save_html(str(session_dir / 'timeline.html'))
    print(f"\n=== RESPUESTA FINAL ===\n{resultado.get('final', 'Sin respuesta')}\n")
    print(f"\nSession ID: {resultado.get('session_id', 'N/A')}")
    print(f"Archivos de sesión:\n - {session_dir / 'events.jsonl'}\n - {md_path}\n - {html_path}\n - {session_dir / 'transcript.json'}")
    print(f"\nSesión persistente guardada en: {session_mgr.sessions_dir}")
    print(f"Para reanudar esta sesión, usa: --session-id {session_id} --resume")
