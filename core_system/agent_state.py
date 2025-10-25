# agent_state.py

"""
Módulo de gestión de estado reactivo y persistente para el sistema de agentes.

Contiene:
- Clases observables (ObservableList, ObservableDict) para detectar cambios.
- ToolSpec: Un artefacto para definir herramientas de forma estructurada.
- ToolRegistry: Un registro que gestiona ToolSpecs y compila su código en demanda.
- ReactiveStateContainer: Un Singleton que gestiona el estado global (tarea, transcript, herramientas)
  y lo persiste en un archivo JSON cada vez que se detecta un cambio.
"""
from __future__ import annotations

import json
import os
import sys
import re
import ast
import traceback
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional

# ===============================
#  Clases Observables
# ===============================
class Observable:
    """Clase base para notificar a los observadores sobre cambios."""
    def __init__(self):
        self._observers: List[Any] = []

    def subscribe(self, observer: Any):
        if observer not in self._observers:
            self._observers.append(observer)

    def notify(self):
        for observer in self._observers:
            observer.update(self)

class ObservableList(list, Observable):
    """Una lista que notifica a los observadores cuando se modifica."""
    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        Observable.__init__(self)

    def append(self, item): super().append(item); self.notify()
    def extend(self, iterable): super().extend(iterable); self.notify()
    def insert(self, index, item): super().insert(index, item); self.notify()
    def remove(self, item): super().remove(item); self.notify()
    def pop(self, *args): res = super().pop(*args); self.notify(); return res
    def clear(self): super().clear(); self.notify()
    def __setitem__(self, key, value): super().__setitem__(key, value); self.notify()
    def __delitem__(self, key): super().__delitem__(key); self.notify()

class ObservableDict(dict, Observable):
    """Un diccionario que notifica a los observadores cuando se modifica."""
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        Observable.__init__(self)

    def __setitem__(self, key, value): super().__setitem__(key, value); self.notify()
    def __delitem__(self, key): super().__delitem__(key); self.notify()
    def pop(self, *args): res = super().pop(*args); self.notify(); return res
    def popitem(self): res = super().popitem(); self.notify(); return res
    def clear(self): super().clear(); self.notify()
    def update(self, *args, **kwargs): super().update(*args, **kwargs); self.notify()

# ===============================
#  Estructura y Registro de Herramientas
# ===============================
@dataclass
class ToolSpec:
    """Artefacto que define una herramienta."""
    name: str
    code: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

def _validate_tool_code(name: str, code: str) -> None:
    """Validación mínima de la herramienta."""
    if not re.match(r"^[a-zA-Z_]\w*$", name):
        raise ValueError(f"Nombre de herramienta inválido: {name}")
    max_chars = int(os.environ.get("TOOL_CODE_MAX_CHARS", "200000"))
    if len(code) > max_chars:
        raise ValueError(f"El código excede el límite de {max_chars} chars.")
    try:
        tree = ast.parse(code)
    except Exception as e:
        raise ValueError(f"El código no compila: {e}")
    func_def = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name), None)
    if func_def is None:
        raise ValueError(f"Debe definirse una función llamada '{name}'.")
    if len(func_def.args.args) != 1:
        raise ValueError("La función debe tener un único parámetro posicional: (args).")

class ToolRegistry:
    """Registro de herramientas que opera con ToolSpec y compila en demanda."""
    def __init__(self):
        self.specs: ObservableDict[str, ToolSpec] = ObservableDict()
        self._compiled_functions: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._dangerous = (os.environ.get("DANGEROUS_TOOLS", "1") != "0")

    def add(self, spec: ToolSpec):
        _validate_tool_code(spec.name, spec.code)
        self.specs[spec.name] = spec
        if spec.name in self._compiled_functions:
            del self._compiled_functions[spec.name]

    def has(self, name: str) -> bool:
        return name in self.specs

    def _compile_and_cache(self, name: str) -> Callable:
        spec = self.specs[name]
        exec_globals = {"__builtins__": __builtins__} if self._dangerous else {"__builtins__": {}}
        exec_locals: Dict[str, Any] = {}
        exec(spec.code, exec_globals, exec_locals)
        fn = exec_locals.get(name) or exec_globals.get(name)
        if not callable(fn):
            raise ValueError(f"No se encontró una función callable llamada '{name}'.")
        self._compiled_functions[name] = fn
        return fn

    def call(self, name: str, args: Dict[str, Any]) -> Any:
        fn = self._compiled_functions.get(name) or self._compile_and_cache(name)
        try:
            return fn(args)
        except Exception:
            return {"ok": False, "error": "Excepción en tool", "traceback": traceback.format_exc(limit=5)}

    def to_dict(self) -> Dict[str, Any]:
        return {name: spec.to_dict() for name, spec in self.specs.items()}

    def load_from_dict(self, data: Dict[str, Any]):
        # Usamos super() para acceder al diccionario base sin disparar notificaciones
        specs_dict = super(ObservableDict, self.specs)
        specs_dict.clear()
        self._compiled_functions.clear()

        for _, spec_data in data.items():
                specs_dict[spec_data['name']] = ToolSpec(name=spec_data['name'], code=spec_data['code'])

        # Notificar una sola vez al final si se cargaron datos
        if data:
            self.specs.notify()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ToolRegistry:
        registry = cls()
        # Esta forma es menos eficiente para la carga inicial porque notifica por cada 'add'.
        for _, spec_data in data.items():
            registry.add(ToolSpec(name=spec_data['name'], code=spec_data['code']))
        return registry
# ===============================
#  Contenedor de Estado
# ===============================
class ReactiveStateContainer:
    """Singleton que contiene el estado del sistema y lo persiste reactivamente."""
    _instance: Optional[ReactiveStateContainer] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ReactiveStateContainer, cls).__new__(cls)
        return cls._instance

    def __init__(self, checkpoint_path: Optional[str] = None):
        if hasattr(self, '_initialized'):
            if checkpoint_path: self.checkpoint_path = checkpoint_path
            return
        self.checkpoint_path = checkpoint_path
        self.task: str = ""
        self.transcript: ObservableList[Dict[str, str]] = ObservableList()
        self.tool_registry: ToolRegistry = ToolRegistry()
        self._subscribe_to_changes()
        self._initialized = True

    def _subscribe_to_changes(self):
        self.transcript.subscribe(self)
        self.tool_registry.specs.subscribe(self)

    def update(self, observable: Any):
        self.save_checkpoint()

    def set_task(self, task: str):
        self.task = task
        self.save_checkpoint()

    def reset_transcript(self):
        self.transcript.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "transcript": list(self.transcript),
            "tool_registry": self.tool_registry.to_dict(),
        }

    def save_checkpoint(self):
        if not self.checkpoint_path: return
        try:
            with open(self.checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error al guardar checkpoint: {e}", file=sys.stderr)
   
    @classmethod
    def load_checkpoint(cls, path: str) -> ReactiveStateContainer:
        """Carga el estado desde un archivo, modificando la instancia en lugar de reemplazarla."""
        instance = cls(checkpoint_path=path)
        if not os.path.exists(path):
            return instance
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # --- INICIO DE LA CORRECCIÓN ---

            # No reemplazar los objetos, modificarlos in-place para mantener las suscripciones.
            instance.task = data.get("task", "")

            # Para la lista, la vaciamos (sin notificar) y luego la extendemos (notificando una vez).
            super(ObservableList, instance.transcript).clear()
            super(ObservableList, instance.transcript).extend(data.get("transcript", []))

            # Para el registro, le pedimos que se cargue a sí mismo desde el diccionario.
            instance.tool_registry.load_from_dict(data.get("tool_registry", {}))

            # Ya no es necesario volver a suscribirse porque los objetos originales nunca se reemplazaron.
            # Se elimina la llamada a `instance._subscribe_to_changes()` de aquí.

            # --- FIN DE LA CORRECCIÓN ---

            print(f"[Estado] Checkpoint cargado desde '{path}'.")
        except Exception as e:
            print(f"Error al cargar checkpoint: {e}. Iniciando estado nuevo.", file=sys.stderr)
        return instance