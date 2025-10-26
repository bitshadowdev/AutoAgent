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

# ===============================
#  Import flexible del cliente LLM
# ===============================
try:
    # Si está en un paquete (p.ej. core_system/llm_client.py)
    from .llm_client import CloudflareLLMClient  # type: ignore
except Exception:
    try:
        from llm_client import CloudflareLLMClient  # type: ignore
    except Exception:
        # Último recurso: agregar el dir actual al path
        sys.path.append(os.path.dirname(__file__))
        from llm_client import CloudflareLLMClient  # type: ignore

# Nuevo: recorder para timeline
from timeline_recorder import Recorder
# Nuevo: gestor de sesiones persistentes
from session_manager import SessionManager

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
#  Validación y ejecución de tools (MODO ABIERTO) + Persistencia
# ===============================

def _validate_tool_ast(name: str, code: str) -> None:
    """Validación mínima: nombre válido, tamaño razonable y que exista la función 'name'.
    En modo abierto **NO** se bloquean imports ni dunders.
    """
    if not re.match(r"^[a-zA-Z_]\w*$", name):
        raise ValueError(f"Nombre de herramienta inválido: {name}")

    max_chars = int(os.environ.get("TOOL_CODE_MAX_CHARS", "200000"))
    if len(code) > max_chars:
        raise ValueError(f"El código de la herramienta excede el límite permitido ({max_chars} chars).")

    try:
        tree = ast.parse(code)
    except Exception as e:
        raise ValueError(f"El código de la herramienta no compila: {e}")

    func_def = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            func_def = node
            break

    if func_def is None:
        raise ValueError(f"Debe definirse una función llamada '{name}'.")

    # Firma: def <name>(args)  (mantenemos un único posicional para coherencia del orquestador)
    args = func_def.args
    if len(args.args) != 1:
        raise ValueError("La función debe tener exactamente un parámetro posicional: (args).")


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

        exec_locals: Dict[str, Any] = {}
        exec(code, exec_globals, exec_locals)
        fn = exec_locals.get(name) or exec_globals.get(name)
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
            return {
                "ok": False,
                "error": f"NameError: {error_str}",
                "suggestion": "Probablemente falta un 'import' al inicio del código. Agrégalo y vuelve a intentar.",
                "traceback": traceback.format_exc(limit=3)
            }
        except ImportError as e:
            return {
                "ok": False,
                "error": f"ImportError: {str(e)}",
                "suggestion": "El módulo no está instalado. Usa subprocess.run(['pip', 'install', 'nombre_modulo']).",
                "traceback": traceback.format_exc(limit=3)
            }
        except KeyError as e:
            return {
                "ok": False,
                "error": f"KeyError: {str(e)}",
                "suggestion": "Falta una clave esperada en el diccionario. Verifica la estructura de datos.",
                "traceback": traceback.format_exc(limit=3)
            }
        except Exception as e:
            return {
                "ok": False,
                "error": f"{type(e).__name__}: {str(e)}",
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
- Llamar una herramienta previamente creada (type='call_tool').

Reglas de herramienta (MODO ABIERTO):
- **Se permiten `import`**, dunders, red (HTTP), sistema de archivos, uso de `subprocess` (p. ej. `pip`).
- **IMPORTANTE: SIEMPRE incluye TODOS los imports necesarios al inicio del código**.
- Si usas `requests`, `json`, `re`, etc., debes importarlos explícitamente.
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
    def __init__(self, llm: CloudflareLLMClient, recorder: Optional[Recorder] = None, session_manager: Optional[SessionManager] = None):
        self.llm = llm
        self.coder = CoderAgent(llm)
        self.supervisor = Supervisor(llm)
        self.tools = ToolRegistry()  # Carga persistentes en el __init__
        self.recorder = recorder
        self.session_manager = session_manager or SessionManager()
        self.current_session_id: Optional[str] = None
        self.tools_used_in_session: List[str] = []

    def _append(self, transcript: List[Dict[str, str]], role: str, content: str) -> None:
        transcript.append({"role": role, "content": content})

    def _print_turn(self, msg: Dict[str, str]) -> None:
        role = msg.get("role", "").upper()
        content = msg.get("content", "")
        print(f"\n[{role}] {content}")

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
                self.tools_used_in_session = loaded.tools_used.copy()
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
        
        turn = len(transcript)  # Continuar desde el último turno
        if self.recorder and not resume_session:
            self.recorder.emit(turn=turn, role="system", etype="run_started", summary=f"task={task}", data={"max_turns": max_turns})

        for _ in range(max_turns):
            turn += 1
            try:
                if self.recorder:
                    self.recorder.emit(turn=turn, role="assistant", etype="coder_step_request", summary="consulta al Coder")
                coder_out = self.coder.step(task, transcript)
                if self.recorder:
                    self.recorder.emit(turn=turn, role="assistant", etype="coder_step_parsed", data={"keys": list(coder_out.keys())}, summary=f"type={coder_out.get('type')}")
            except Exception as e:
                if self.recorder:
                    self.recorder.emit(turn=turn, role="assistant", etype="coder_parse_error", summary=str(e))
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
                    path = self.recorder.write_blob(f"final/turn_{turn:03d}_answer.txt", answer)
                    self.recorder.emit(turn=turn, role="assistant", etype="coder_final_proposal", summary=message, data={"answer_path": path})
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
                        code_path = self.recorder.write_blob(f"tools_session/turn_{turn:03d}_{tname}.py", code)
                        self.recorder.emit(turn=turn, role="assistant", etype=event_type, summary=f"def {tname}(args) - {action}", data={"code_path": code_path, "chars": len(code), "is_update": is_update})
                    
                    # Registrar en memoria y **persistir** (permite sobrescritura)
                    self.tools.add_from_code(tname, code)
                    
                    if self.recorder:
                        self.recorder.emit(turn=turn, role="assistant", etype="tool_registered", data={"name": tname, "persistent_dir": str(self.tools.store_dir), "action": action})
                    
                    # Mostrar mensaje informativo si es actualización
                    if is_update and stream:
                        print(f"\n[⟳ HERRAMIENTA ACTUALIZADA] {tname} ha sido corregida/mejorada.")
                    
                    name = tname

                # Ejecutar herramienta
                if self.recorder:
                    self.recorder.emit(turn=turn, role="assistant", etype="tool_call", summary=f"{name}(args)", data={"args": args})
                result = self.tools.call(name, args)
                # Rastrear herramientas usadas
                if name not in self.tools_used_in_session:
                    self.tools_used_in_session.append(name)
                
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
                        error_msg += f"\nTraceback: {traceback_info}"
                    elif "error" in result and result["error"]:
                        error_msg = f"\n\n⚠️ ERROR EN HERRAMIENTA: {result['error']}"
                
                self._append(
                    transcript,
                    'assistant',
                    f"[Coder] {msg}\n\nHerramienta usada: {name}\nArgs: {args}\nResultado: {result}{error_msg}"
                )
                if self.recorder:
                    if isinstance(result, dict) and result.get("ok") is False:
                        self.recorder.emit(turn=turn, role="assistant", etype="tool_result_error", data={"name": name, "error": result.get("error"), "traceback": result.get("traceback")})
                    else:
                        self.recorder.emit(turn=turn, role="assistant", etype="tool_result_ok", data={"name": name, "result": result})
                if stream: self._print_turn(transcript[-1])

            else:
                self._append(transcript, 'assistant', f"[Coder] Tipo desconocido: {ctype}. Solicito nuevo intento.")
                if stream: self._print_turn(transcript[-1])

            # Decisión del supervisor
            try:
                decision = self.supervisor.decide(task, transcript)
                route = (decision.get('route') or '').lower()
                if self.recorder:
                    self.recorder.emit(turn=turn, role="assistant", etype="supervisor_decision", data=decision, summary=f"route={route}")
            except Exception as e:
                route = 'coder'
                self._append(transcript, 'assistant', f"[Supervisor] Error interpretando decisión: {e}. Continuar con coder.")
                if stream: self._print_turn(transcript[-1])

            if route == 'end':
                last = next((m for m in reversed(transcript) if m['role'] == 'assistant'), None)
                final = last['content'] if last else 'Tarea finalizada.'
                # Guardar sesión persistente
                if self.current_session_id:
                    self.session_manager.save_session(
                        session_id=self.current_session_id,
                        transcript=transcript,
                        metadata={"task": task, "total_turns": turn, "model": self.coder.model},
                        tools_used=self.tools_used_in_session,
                        status="completed"
                    )
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
                self.recorder.emit(turn=turn, role="assistant", etype="iteration_continue")
            if stream: self._print_turn(transcript[-1])
            
            # Guardar progreso de sesión cada turno
            if self.current_session_id:
                self.session_manager.save_session(
                    session_id=self.current_session_id,
                    transcript=transcript,
                    metadata={"task": task, "total_turns": turn, "model": self.coder.model},
                    tools_used=self.tools_used_in_session,
                    status="active"
                )

        last = next((m for m in reversed(transcript) if m['role'] == 'assistant'), None)
        final = last['content'] if last else 'No se pudo completar en los turnos permitidos.'
        # Guardar sesión (estado: activa porque no se completó)
        if self.current_session_id:
            self.session_manager.save_session(
                session_id=self.current_session_id,
                transcript=transcript,
                metadata={"task": task, "total_turns": turn, "model": self.coder.model},
                tools_used=self.tools_used_in_session,
                status="active"
            )
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
    # Nuevos argumentos para sesiones
    parser.add_argument('--session-id', dest='session_id', help='ID de la sesión (auto-generado si no se especifica).')
    parser.add_argument('--resume', dest='resume_session', action='store_true', help='Reanudar sesión anterior especificada con --session-id.')
    parser.add_argument('--sessions-list', dest='sessions_list', action='store_true', help='Listar sesiones guardadas y salir.')
    parser.add_argument('--sessions-dir', dest='sessions_dir', default='.sessions', help='Directorio de sesiones persistentes.')
    parser.add_argument('--delete-session', dest='delete_session', help='Eliminar una sesión por ID.')
    args = parser.parse_args()

    # Definir carpeta de sesión
    session_dir = Path(args.log_dir) / datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    recorder = Recorder(str(session_dir))

    # Respetar --tools-dir
    os.environ['TOOL_STORE_DIR'] = args.tools_dir
    
    # Crear gestor de sesiones
    session_mgr = SessionManager(args.sessions_dir)

    system = MiniAgentSystem(llm, recorder=recorder, session_manager=session_mgr)

    # Comando: listar tools
    if args.tools_list:
        print("Tools persistentes en", system.tools.store_dir)
        for name in system.tools.list():
            print(" -", name)
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
