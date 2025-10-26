"""
Sistema de EventBus centralizado para broadcasting de eventos en tiempo real.

Permite que múltiples listeners (como un dashboard Streamlit) reciban eventos
del sistema sin modificar el flujo de ejecución existente.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from threading import Lock
import json
from pathlib import Path


def _now_iso() -> str:
    """Timestamp ISO con timezone UTC."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SystemEvent:
    """Evento del sistema con toda la información relevante."""
    
    # Metadata básica
    ts: str
    turn: int
    role: str  # "coder", "supervisor", "agent", "user", "system", "tool"
    etype: str  # Tipo de evento específico
    
    # Contenido
    summary: str
    data: Dict[str, Any]
    
    # Contexto adicional
    session_id: Optional[str] = None
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a diccionario."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convierte el evento a JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class EventBus:
    """
    Bus de eventos centralizado con soporte para múltiples listeners.
    
    Thread-safe para poder emitir eventos desde cualquier parte del sistema.
    """
    
    def __init__(self):
        self._listeners: List[Callable[[SystemEvent], None]] = []
        self._lock = Lock()
        self._event_history: List[SystemEvent] = []
        self._max_history = 1000  # Mantener últimos 1000 eventos en memoria
        
    def subscribe(self, listener: Callable[[SystemEvent], None]) -> None:
        """
        Registra un listener que será llamado con cada evento.
        
        Args:
            listener: Función que recibe un SystemEvent
        """
        with self._lock:
            self._listeners.append(listener)
    
    def unsubscribe(self, listener: Callable[[SystemEvent], None]) -> None:
        """Desregistra un listener."""
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)
    
    def emit(
        self,
        *,
        turn: int,
        role: str,
        etype: str,
        summary: str = "",
        data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        tool_name: Optional[str] = None
    ) -> SystemEvent:
        """
        Emite un evento a todos los listeners registrados.
        
        Args:
            turn: Número de turno
            role: Rol del emisor (coder, supervisor, agent, user, system, tool)
            etype: Tipo específico de evento
            summary: Resumen corto del evento
            data: Datos adicionales del evento
            session_id: ID de sesión actual
            agent_name: Nombre del agente (si aplica)
            tool_name: Nombre de la herramienta (si aplica)
        
        Returns:
            El evento creado
        """
        event = SystemEvent(
            ts=_now_iso(),
            turn=turn,
            role=role,
            etype=etype,
            summary=summary,
            data=data or {},
            session_id=session_id,
            agent_name=agent_name,
            tool_name=tool_name
        )
        
        # Agregar a historial (limitado)
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
            
            # Notificar a todos los listeners
            for listener in self._listeners:
                try:
                    listener(event)
                except Exception as e:
                    # No dejar que un listener roto bloquee otros
                    print(f"[EventBus] Error en listener: {e}")
        
        return event
    
    def get_history(self, limit: Optional[int] = None) -> List[SystemEvent]:
        """
        Obtiene el historial de eventos.
        
        Args:
            limit: Número máximo de eventos a retornar (más recientes)
        
        Returns:
            Lista de eventos
        """
        with self._lock:
            if limit is None:
                return self._event_history.copy()
            return self._event_history[-limit:]
    
    def clear_history(self) -> None:
        """Limpia el historial de eventos."""
        with self._lock:
            self._event_history.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del bus de eventos."""
        with self._lock:
            stats = {
                "total_listeners": len(self._listeners),
                "total_events": len(self._event_history),
                "max_history": self._max_history,
                "events_by_type": {},
                "events_by_role": {}
            }
            
            for event in self._event_history:
                # Contar por tipo
                stats["events_by_type"][event.etype] = stats["events_by_type"].get(event.etype, 0) + 1
                # Contar por rol
                stats["events_by_role"][event.role] = stats["events_by_role"].get(event.role, 0) + 1
            
            return stats


# Instancia global del EventBus
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Obtiene la instancia global del EventBus (singleton)."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


class EventLogger:
    """
    Logger de eventos a archivo JSONL.
    
    Se puede usar como listener del EventBus para guardar eventos a disco.
    """
    
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Crear archivo si no existe
        if not self.log_path.exists():
            self.log_path.touch()
    
    def __call__(self, event: SystemEvent) -> None:
        """Llamado por el EventBus cuando hay un nuevo evento."""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(event.to_json() + "\n")
    
    @staticmethod
    def read_events(log_path: str) -> List[SystemEvent]:
        """Lee eventos desde un archivo JSONL."""
        events = []
        path = Path(log_path)
        
        if not path.exists():
            return events
        
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        events.append(SystemEvent(**data))
                    except Exception:
                        continue
        
        return events


# Helpers para emitir eventos comunes

def emit_message(
    turn: int,
    sender: str,
    content: str,
    message_type: str = "chat",
    session_id: Optional[str] = None
) -> None:
    """Emite un evento de mensaje (usuario, agente, etc.)."""
    bus = get_event_bus()
    bus.emit(
        turn=turn,
        role=sender,
        etype=f"message_{message_type}",
        summary=content[:200],
        data={"content": content, "message_type": message_type},
        session_id=session_id
    )


def emit_tool_created(
    turn: int,
    tool_name: str,
    code: str,
    is_update: bool = False,
    session_id: Optional[str] = None
) -> None:
    """Emite un evento de creación/actualización de herramienta."""
    bus = get_event_bus()
    bus.emit(
        turn=turn,
        role="coder",
        etype="tool_created" if not is_update else "tool_updated",
        summary=f"{'Actualizada' if is_update else 'Creada'} herramienta: {tool_name}",
        data={
            "tool_name": tool_name,
            "code": code,
            "code_length": len(code),
            "is_update": is_update
        },
        session_id=session_id,
        tool_name=tool_name
    )


def emit_tool_called(
    turn: int,
    tool_name: str,
    args: Dict[str, Any],
    session_id: Optional[str] = None
) -> None:
    """Emite un evento de invocación de herramienta."""
    bus = get_event_bus()
    bus.emit(
        turn=turn,
        role="tool",
        etype="tool_called",
        summary=f"Llamada a herramienta: {tool_name}",
        data={"tool_name": tool_name, "args": args},
        session_id=session_id,
        tool_name=tool_name
    )


def emit_tool_result(
    turn: int,
    tool_name: str,
    result: Any,
    success: bool = True,
    session_id: Optional[str] = None
) -> None:
    """Emite un evento de resultado de herramienta."""
    bus = get_event_bus()
    bus.emit(
        turn=turn,
        role="tool",
        etype="tool_result_ok" if success else "tool_result_error",
        summary=f"Resultado de {tool_name}: {'OK' if success else 'ERROR'}",
        data={
            "tool_name": tool_name,
            "result": result,
            "success": success
        },
        session_id=session_id,
        tool_name=tool_name
    )


def emit_agent_action(
    turn: int,
    agent_name: str,
    action: str,
    details: Dict[str, Any],
    session_id: Optional[str] = None
) -> None:
    """Emite un evento de acción de agente."""
    bus = get_event_bus()
    bus.emit(
        turn=turn,
        role="agent",
        etype=f"agent_{action}",
        summary=f"Agente {agent_name}: {action}",
        data={"agent_name": agent_name, "action": action, **details},
        session_id=session_id,
        agent_name=agent_name
    )
