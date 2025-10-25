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
        except Exception:
            return {
                "ok": False,
                "error": "Excepción en tool",
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

Guía para 'tips':
- Sé específico y verificable (p.ej., “agrega pruebas para X”, “maneja error Y”, “cubre caso límite Z”).
- Incluye, cuando aplique: siguiente acción, cómo validarla, y un criterio de salida.
- Enfoca en brechas observables: pruebas, manejo de errores, casos límite, rendimiento, seguridad, UX, fuentes/citas, estructura del código.
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
    def __init__(self, llm: CloudflareLLMClient, recorder: Optional[Recorder] = None):
        self.llm = llm
        self.coder = CoderAgent(llm)
        self.supervisor = Supervisor(llm)
        self.tools = ToolRegistry()  # Carga persistentes en el __init__
        self.recorder = recorder

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
    ) -> Dict[str, Any]:
        transcript: List[Dict[str, str]] = []
        turn = 0
        if self.recorder:
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
                    if not self.tools.has(tname):
                        if self.recorder:
                            code_path = self.recorder.write_blob(f"tools_session/turn_{turn:03d}_{tname}.py", code)
                            self.recorder.emit(turn=turn, role="assistant", etype="tool_create", summary=f"def {tname}(args)", data={"code_path": code_path, "chars": len(code)})
                        # Registrar en memoria y **persistir**
                        self.tools.add_from_code(tname, code)
                        if self.recorder:
                            self.recorder.emit(turn=turn, role="assistant", etype="tool_registered", data={"name": tname, "persistent_dir": str(self.tools.store_dir)})
                    name = tname

                # Ejecutar herramienta
                if self.recorder:
                    self.recorder.emit(turn=turn, role="assistant", etype="tool_call", summary=f"{name}(args)", data={"args": args})
                result = self.tools.call(name, args)
                self._append(
                    transcript,
                    'assistant',
                    f"[Coder] {msg}\n\nHerramienta usada: {name}\nArgs: {args}\nResultado: {result}"
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
                return {"final": final, "transcript": transcript}

            # Feedback genérico para otra vuelta
            self._append(transcript, 'user', '[Supervisor] Continúa, falta completar o mejorar la respuesta.')
            if self.recorder:
                self.recorder.emit(turn=turn, role="assistant", etype="iteration_continue")
            if stream: self._print_turn(transcript[-1])

        last = next((m for m in reversed(transcript) if m['role'] == 'assistant'), None)
        final = last['content'] if last else 'No se pudo completar en los turnos permitidos.'
        if save_transcript_path:
            try:
                with open(save_transcript_path, "w", encoding="utf-8") as f:
                    import json as _json
                    _json.dump(transcript, f, ensure_ascii=False, indent=2)
            except Exception as _:
                pass
        return {"final": final, "transcript": transcript}


# ===============================
#  Ejecución directa
# ===============================
if __name__ == '__main__':
    llm = CloudflareLLMClient()
    # --- CLI extendido ---
    parser = argparse.ArgumentParser(description='Mini sistema de agentes (supervisor + coder) con tools persistentes.')
    parser.add_argument('-q', '--question', '--task', dest='task', help='Tarea o pregunta a resolver.')
    parser.add_argument('-m', '--max-turns', dest='max_turns', type=int, default=5, help='Máximo de turnos.')
    parser.add_argument('--log-dir', dest='log_dir', default='.runs', help='Directorio base para logs/timeline.')
    parser.add_argument('--tools-list', action='store_true', help='Listar tools persistentes y salir.')
    parser.add_argument('--tools-dir', dest='tools_dir', default=os.environ.get('TOOL_STORE_DIR', '.permanent_tools'), help='Directorio de tools persistentes.')
    args = parser.parse_args()

    # Definir carpeta de sesión
    session_dir = Path(args.log_dir) / datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    recorder = Recorder(str(session_dir))

    # Respetar --tools-dir
    os.environ['TOOL_STORE_DIR'] = args.tools_dir

    system = MiniAgentSystem(llm, recorder=recorder)

    if args.tools_list:
        print("Tools persistentes en", system.tools.store_dir)
        for name in system.tools.list():
            print(" -", name)
        raise SystemExit(0)

    tarea = (
        args.task
        or os.environ.get('AGENT_TASK')
        or input('Escribe tu pregunta/tarea: ').strip()
        or 'Escribe una tool que scrappee 10 titulares de https://www.latercera.com/ y devuélvelos en lista.'
    )

    # Guardamos también el transcript en la sesión
    resultado = system.run(tarea, max_turns=args.max_turns, save_transcript_path=str(session_dir / 'transcript.json'))

    # Compilamos timeline legible
    md_path = recorder.save_markdown(str(session_dir / 'timeline.md'))
    html_path = recorder.save_html(str(session_dir / 'timeline.html'))
    print(f"\n=== RESPUESTA FINAL ===\n{resultado}\n")
    print(f"Archivos de sesión:\n - {session_dir / 'events.jsonl'}\n - {md_path}\n - {html_path}\n - {session_dir / 'transcript.json'}")
