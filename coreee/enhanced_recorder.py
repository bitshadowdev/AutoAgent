"""
Enhanced Recorder que extiende el Recorder original con EventBus para tiempo real.

Mantiene compatibilidad total con el Recorder existente mientras agrega broadcasting.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from coreee.timeline_recorder import Recorder, Event
from coreee.event_bus import get_event_bus, SystemEvent


class EnhancedRecorder(Recorder):
    """
    Recorder mejorado que emite eventos al EventBus en tiempo real.
    
    Mantiene toda la funcionalidad del Recorder original (JSONL, Markdown, HTML)
    y además emite eventos al EventBus global para visualización en tiempo real.
    """
    
    def __init__(self, root: str, session_id: Optional[str] = None):
        super().__init__(root)
        self.session_id = session_id
        self.event_bus = get_event_bus()
    
    def emit(
        self,
        *,
        turn: int,
        role: str,
        etype: str,
        summary: str = "",
        data: Optional[Dict[str, Any]] = None
    ) -> Event:
        """
        Emite un evento al Recorder original Y al EventBus.
        
        Mantiene compatibilidad 100% con el Recorder original.
        """
        # Llamar al Recorder original
        event = super().emit(
            turn=turn,
            role=role,
            etype=etype,
            summary=summary,
            data=data
        )
        
        # Emitir al EventBus para tiempo real
        self._emit_to_bus(turn, role, etype, summary, data or {})
        
        return event
    
    def _emit_to_bus(
        self,
        turn: int,
        role: str,
        etype: str,
        summary: str,
        data: Dict[str, Any]
    ) -> None:
        """Emite evento al EventBus con contexto adicional."""
        
        # Extraer información relevante según el tipo de evento
        agent_name = None
        tool_name = None
        
        if "agent" in etype.lower():
            agent_name = data.get("agent_name") or data.get("name")
        
        if "tool" in etype.lower():
            tool_name = data.get("tool_name") or data.get("name")
        
        # Emitir al bus
        self.event_bus.emit(
            turn=turn,
            role=role,
            etype=etype,
            summary=summary,
            data=data,
            session_id=self.session_id,
            agent_name=agent_name,
            tool_name=tool_name
        )
    
    # Métodos adicionales para eventos específicos
    
    def emit_user_message(self, turn: int, content: str) -> None:
        """Emite un mensaje del usuario."""
        self.emit(
            turn=turn,
            role="user",
            etype="user_message",
            summary=content[:200],
            data={"content": content}
        )
    
    def emit_coder_message(self, turn: int, content: str, action: Optional[str] = None) -> None:
        """Emite un mensaje del Coder."""
        self.emit(
            turn=turn,
            role="coder",
            etype=f"coder_{action}" if action else "coder_message",
            summary=content[:200],
            data={"content": content, "action": action}
        )
    
    def emit_supervisor_message(self, turn: int, decision: str, reasoning: str = "") -> None:
        """Emite un mensaje del Supervisor."""
        self.emit(
            turn=turn,
            role="supervisor",
            etype="supervisor_decision",
            summary=f"Decisión: {decision}",
            data={"decision": decision, "reasoning": reasoning}
        )
    
    def emit_tool_creation(
        self,
        turn: int,
        tool_name: str,
        code: str,
        is_update: bool = False
    ) -> None:
        """Emite evento de creación/actualización de herramienta."""
        self.emit(
            turn=turn,
            role="coder",
            etype="tool_updated" if is_update else "tool_created",
            summary=f"{'Actualizada' if is_update else 'Creada'} herramienta: {tool_name}",
            data={
                "tool_name": tool_name,
                "code": code,
                "code_length": len(code),
                "is_update": is_update
            }
        )
    
    def emit_tool_invocation(
        self,
        turn: int,
        tool_name: str,
        args: Dict[str, Any]
    ) -> None:
        """Emite evento de invocación de herramienta."""
        self.emit(
            turn=turn,
            role="tool",
            etype="tool_invocation",
            summary=f"Llamando a: {tool_name}",
            data={"tool_name": tool_name, "args": args}
        )
    
    def emit_tool_result(
        self,
        turn: int,
        tool_name: str,
        result: Any,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Emite evento de resultado de herramienta."""
        self.emit(
            turn=turn,
            role="tool",
            etype="tool_result_ok" if success else "tool_result_error",
            summary=f"{tool_name}: {'OK' if success else 'ERROR'}",
            data={
                "tool_name": tool_name,
                "result": result,
                "success": success,
                "error": error
            }
        )
    
    def emit_agent_created(
        self,
        turn: int,
        agent_name: str,
        role_desc: str,
        capabilities: list
    ) -> None:
        """Emite evento de creación de agente."""
        self.emit(
            turn=turn,
            role="system",
            etype="agent_created",
            summary=f"Creado agente: {agent_name} ({role_desc})",
            data={
                "agent_name": agent_name,
                "role": role_desc,
                "capabilities": capabilities
            }
        )
    
    def emit_agent_invocation(
        self,
        turn: int,
        agent_name: str,
        task: str
    ) -> None:
        """Emite evento de invocación de agente."""
        self.emit(
            turn=turn,
            role="agent",
            etype="agent_invoked",
            summary=f"Invocando agente: {agent_name}",
            data={"agent_name": agent_name, "task": task}
        )
    
    def emit_agent_response(
        self,
        turn: int,
        agent_name: str,
        response: str
    ) -> None:
        """Emite evento de respuesta de agente."""
        self.emit(
            turn=turn,
            role="agent",
            etype="agent_response",
            summary=f"Respuesta de {agent_name}",
            data={"agent_name": agent_name, "response": response[:500]}
        )
    
    def emit_session_start(self, turn: int, task: str) -> None:
        """Emite evento de inicio de sesión."""
        self.emit(
            turn=turn,
            role="system",
            etype="session_start",
            summary=f"Iniciando sesión: {self.session_id or 'unnamed'}",
            data={"task": task, "session_id": self.session_id}
        )
    
    def emit_session_end(self, turn: int, status: str, summary: str = "") -> None:
        """Emite evento de fin de sesión."""
        self.emit(
            turn=turn,
            role="system",
            etype="session_end",
            summary=f"Sesión finalizada: {status}",
            data={"status": status, "summary": summary}
        )
    
    def emit_error(self, turn: int, error_type: str, message: str, traceback: Optional[str] = None) -> None:
        """Emite evento de error."""
        self.emit(
            turn=turn,
            role="system",
            etype=f"error_{error_type}",
            summary=f"Error: {message}",
            data={"error_type": error_type, "message": message, "traceback": traceback}
        )


def create_recorder(root: str, session_id: Optional[str] = None, use_enhanced: bool = True) -> Recorder:
    """
    Factory para crear recorders.
    
    Args:
        root: Directorio raíz para logs
        session_id: ID de sesión
        use_enhanced: Si True, usa EnhancedRecorder (con EventBus)
    
    Returns:
        Recorder o EnhancedRecorder
    """
    if use_enhanced:
        return EnhancedRecorder(root, session_id)
    return Recorder(root)
