"""
Sistema de persistencia de sesiones para agentes.

Permite guardar y cargar:
- Historial de conversaciones (transcript)
- Estado de agentes
- Configuraciones
- Metadatos de sesión

Uso:
    manager = SessionManager()
    
    # Guardar sesión
    manager.save_session(
        session_id="mi_sesion",
        transcript=transcript,
        metadata={"task": "...", "turns": 5}
    )
    
    # Cargar sesión
    session = manager.load_session("mi_sesion")
    
    # Listar sesiones
    sessions = manager.list_sessions()
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import json
from typing import Any, Dict, List, Optional


@dataclass
class SessionMetadata:
    """Metadatos de una sesión"""
    session_id: str
    task: str
    created_at: str
    updated_at: str
    total_turns: int
    status: str  # active, completed, error
    model: str
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SessionMetadata:
        return cls(**data)


@dataclass
class SessionData:
    """Datos completos de una sesión"""
    metadata: SessionMetadata
    transcript: List[Dict[str, str]]
    tools_used: List[str]
    custom_data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "transcript": self.transcript,
            "tools_used": self.tools_used,
            "custom_data": self.custom_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SessionData:
        return cls(
            metadata=SessionMetadata.from_dict(data["metadata"]),
            transcript=data.get("transcript", []),
            tools_used=data.get("tools_used", []),
            custom_data=data.get("custom_data", {})
        )


class SessionManager:
    """Gestor de sesiones persistentes"""
    
    def __init__(self, sessions_dir: str = ".sessions"):
        self.sessions_dir = Path(sessions_dir).resolve()
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.sessions_dir / "index.json"
        self._load_index()
    
    def _load_index(self) -> None:
        """Carga el índice de sesiones"""
        if self.index_file.exists():
            try:
                data = json.loads(self.index_file.read_text(encoding="utf-8"))
                self.index = data
            except Exception:
                self.index = {"sessions": {}}
        else:
            self.index = {"sessions": {}}
    
    def _save_index(self) -> None:
        """Guarda el índice de sesiones"""
        tmp = self.index_file.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self.index, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        tmp.replace(self.index_file)
    
    def _session_path(self, session_id: str) -> Path:
        """Obtiene la ruta del archivo de sesión"""
        # Sanitizar el ID
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
        return self.sessions_dir / f"{safe_id}.json"
    
    def save_session(
        self,
        session_id: str,
        transcript: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None,
        tools_used: Optional[List[str]] = None,
        custom_data: Optional[Dict[str, Any]] = None,
        status: str = "active"
    ) -> SessionData:
        """Guarda una sesión completa"""
        now = datetime.utcnow().isoformat() + "Z"
        
        # Crear o actualizar metadata
        if session_id in self.index["sessions"]:
            # Actualizar sesión existente
            existing = self.index["sessions"][session_id]
            session_metadata = SessionMetadata(
                session_id=session_id,
                task=metadata.get("task", existing.get("task", "")),
                created_at=existing.get("created_at", now),
                updated_at=now,
                total_turns=metadata.get("total_turns", len(transcript)),
                status=status,
                model=metadata.get("model", existing.get("model", "default")),
                tags=metadata.get("tags", existing.get("tags", []))
            )
        else:
            # Nueva sesión
            session_metadata = SessionMetadata(
                session_id=session_id,
                task=metadata.get("task", "") if metadata else "",
                created_at=now,
                updated_at=now,
                total_turns=metadata.get("total_turns", len(transcript)) if metadata else len(transcript),
                status=status,
                model=metadata.get("model", "default") if metadata else "default",
                tags=metadata.get("tags", []) if metadata else []
            )
        
        # Crear datos de sesión
        session_data = SessionData(
            metadata=session_metadata,
            transcript=transcript,
            tools_used=tools_used or [],
            custom_data=custom_data or {}
        )
        
        # Guardar archivo de sesión
        session_path = self._session_path(session_id)
        session_path.write_text(
            json.dumps(session_data.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # Actualizar índice
        self.index["sessions"][session_id] = {
            "path": str(session_path),
            "task": session_metadata.task,
            "created_at": session_metadata.created_at,
            "updated_at": session_metadata.updated_at,
            "status": session_metadata.status,
            "model": session_metadata.model,
            "tags": session_metadata.tags
        }
        self._save_index()
        
        return session_data
    
    def load_session(self, session_id: str) -> Optional[SessionData]:
        """Carga una sesión"""
        if session_id not in self.index["sessions"]:
            return None
        
        session_path = self._session_path(session_id)
        if not session_path.exists():
            return None
        
        try:
            data = json.loads(session_path.read_text(encoding="utf-8"))
            return SessionData.from_dict(data)
        except Exception:
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Elimina una sesión"""
        if session_id not in self.index["sessions"]:
            return False
        
        session_path = self._session_path(session_id)
        if session_path.exists():
            session_path.unlink()
        
        del self.index["sessions"][session_id]
        self._save_index()
        return True
    
    def list_sessions(
        self,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Lista todas las sesiones con filtros opcionales"""
        sessions = []
        
        for session_id, meta in self.index["sessions"].items():
            # Filtrar por status
            if status and meta.get("status") != status:
                continue
            
            # Filtrar por tags
            if tags:
                session_tags = set(meta.get("tags", []))
                if not any(tag in session_tags for tag in tags):
                    continue
            
            sessions.append({
                "session_id": session_id,
                **meta
            })
        
        # Ordenar por fecha de actualización (más reciente primero)
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        # Limitar resultados
        if limit:
            sessions = sessions[:limit]
        
        return sessions
    
    def get_latest_session(self, status: Optional[str] = None) -> Optional[str]:
        """Obtiene el ID de la sesión más reciente"""
        sessions = self.list_sessions(status=status, limit=1)
        return sessions[0]["session_id"] if sessions else None
    
    def session_exists(self, session_id: str) -> bool:
        """Verifica si existe una sesión"""
        return session_id in self.index["sessions"]
    
    def add_to_transcript(
        self,
        session_id: str,
        message: Dict[str, str]
    ) -> bool:
        """Agrega un mensaje al transcript de una sesión existente"""
        session = self.load_session(session_id)
        if not session:
            return False
        
        session.transcript.append(message)
        session.metadata.updated_at = datetime.utcnow().isoformat() + "Z"
        session.metadata.total_turns = len(session.transcript)
        
        # Guardar sesión actualizada
        self.save_session(
            session_id=session_id,
            transcript=session.transcript,
            metadata=session.metadata.to_dict(),
            tools_used=session.tools_used,
            custom_data=session.custom_data,
            status=session.metadata.status
        )
        return True
    
    def update_session_status(self, session_id: str, status: str) -> bool:
        """Actualiza el estado de una sesión"""
        session = self.load_session(session_id)
        if not session:
            return False
        
        session.metadata.status = status
        session.metadata.updated_at = datetime.utcnow().isoformat() + "Z"
        
        self.save_session(
            session_id=session_id,
            transcript=session.transcript,
            metadata=session.metadata.to_dict(),
            tools_used=session.tools_used,
            custom_data=session.custom_data,
            status=status
        )
        return True
