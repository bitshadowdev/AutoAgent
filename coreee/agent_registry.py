"""
Sistema de registro y gestión de agentes dinámicos.

Permite crear agentes especializados durante la ejecución que pueden:
- Tener prompts personalizados
- Especializarse en tareas específicas
- Ser creados por el Coder
- Persistir en sesiones
- Interactuar con otros agentes

Ejemplo de agente especializado:
    {
        "name": "data_analyst",
        "role": "Analista de Datos",
        "system_prompt": "Eres un experto en análisis de datos...",
        "capabilities": ["análisis", "visualización", "estadísticas"]
    }
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class AgentDefinition:
    """Define un agente especializado"""
    name: str
    role: str
    system_prompt: str
    capabilities: List[str]
    created_at: str
    created_by: str  # "coder" o nombre del agente creador
    temperature: float = 0.7
    max_tokens: int = 1500
    model: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentDefinition:
        return cls(**data)


class DynamicAgent:
    """Agente dinámico que puede participar en conversaciones"""
    
    def __init__(self, definition: AgentDefinition, llm):
        self.definition = definition
        self.llm = llm
        self.name = definition.name
        self.role = definition.role
        self.history: List[Dict[str, str]] = []
    
    def step(self, task: str, context: List[Dict[str, str]]) -> str:
        """
        Ejecuta un paso del agente.
        
        Args:
            task: Tarea específica para este agente
            context: Contexto de la conversación (mensajes previos)
        
        Returns:
            Respuesta del agente como texto
        """
        # Construir mensajes con el system_prompt del agente
        messages = [
            {"role": "system", "content": self.definition.system_prompt},
            *context[-5:],  # Últimos 5 mensajes para contexto
            {"role": "user", "content": f"Tarea para {self.role}: {task}"}
        ]
        
        # Debug: imprimir que se está usando el prompt del agente
        print(f"\n[DEBUG AGENT] Usando agente '{self.name}' ({self.role})")
        print(f"[DEBUG AGENT] System prompt (primeros 100 chars): {self.definition.system_prompt[:100]}...")
        print(f"[DEBUG AGENT] Capacidades: {', '.join(self.definition.capabilities)}")
        print(f"[DEBUG AGENT] Tarea: {task}\n")
        
        response = self.llm.chat(
            messages,
            model=self.definition.model or '@cf/openai/gpt-oss-120b',
            temperature=self.definition.temperature,
            max_tokens=self.definition.max_tokens
        )
        
        return response
    
    def __repr__(self) -> str:
        return f"DynamicAgent(name={self.name}, role={self.role})"


class AgentRegistry:
    """Registro de agentes dinámicos en una sesión"""
    
    def __init__(self, llm, agents_dir: str = ".agents"):
        self.llm = llm
        self.agents_dir = Path(agents_dir).resolve()
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.agents_dir / "manifest.json"
        
        # Agentes activos en memoria
        self._agents: Dict[str, DynamicAgent] = {}
        
        # Cargar manifest
        self._manifest = self._load_manifest()
        
        # Cargar agentes persistidos
        self.load_persisted_agents()
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Carga el manifest de agentes"""
        if self.manifest_file.exists():
            try:
                return json.loads(self.manifest_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"agents": {}}
    
    def _save_manifest(self) -> None:
        """Guarda el manifest de agentes"""
        tmp = self.manifest_file.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self._manifest, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        tmp.replace(self.manifest_file)
    
    def _agent_path(self, name: str) -> Path:
        """Ruta del archivo de definición del agente"""
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name).strip("_") or "agent"
        return self.agents_dir / f"{safe_name}.json"
    
    def create_agent(
        self,
        name: str,
        role: str,
        system_prompt: str,
        capabilities: List[str],
        created_by: str = "coder",
        temperature: float = 0.7,
        max_tokens: int = 1500,
        model: Optional[str] = None
    ) -> DynamicAgent:
        """
        Crea un nuevo agente dinámico.
        
        Args:
            name: Nombre único del agente (ej: "data_analyst")
            role: Rol descriptivo (ej: "Analista de Datos")
            system_prompt: Prompt del sistema para el agente
            capabilities: Lista de capacidades del agente
            created_by: Quién creó el agente
            temperature: Temperatura para generación
            max_tokens: Máximo de tokens
            model: Modelo específico (opcional)
        
        Returns:
            DynamicAgent creado
        """
        now = datetime.utcnow().isoformat() + "Z"
        
        definition = AgentDefinition(
            name=name,
            role=role,
            system_prompt=system_prompt,
            capabilities=capabilities,
            created_at=now,
            created_by=created_by,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model
        )
        
        # Crear instancia del agente
        agent = DynamicAgent(definition, self.llm)
        
        # Registrar en memoria
        self._agents[name] = agent
        
        # Persistir a disco
        self._persist_agent(definition)
        
        return agent
    
    def _persist_agent(self, definition: AgentDefinition) -> None:
        """Persiste un agente a disco"""
        agent_file = self._agent_path(definition.name)
        agent_file.write_text(
            json.dumps(definition.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # Actualizar manifest
        self._manifest["agents"][definition.name] = {
            "path": str(agent_file),
            "role": definition.role,
            "created_at": definition.created_at,
            "created_by": definition.created_by,
            "capabilities": definition.capabilities
        }
        self._save_manifest()
    
    def load_persisted_agents(self) -> int:
        """Carga agentes persistidos del disco"""
        loaded = 0
        
        for name, meta in self._manifest.get("agents", {}).items():
            if name in self._agents:
                continue
            
            try:
                agent_file = Path(meta.get("path", ""))
                if agent_file.exists():
                    data = json.loads(agent_file.read_text(encoding="utf-8"))
                    definition = AgentDefinition.from_dict(data)
                    agent = DynamicAgent(definition, self.llm)
                    self._agents[name] = agent
                    loaded += 1
            except Exception:
                continue
        
        return loaded
    
    def get_agent(self, name: str) -> Optional[DynamicAgent]:
        """Obtiene un agente por nombre"""
        return self._agents.get(name)
    
    def has_agent(self, name: str) -> bool:
        """Verifica si existe un agente"""
        return name in self._agents
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """Lista todos los agentes con sus metadatos"""
        agents_list = []
        for name, agent in self._agents.items():
            agents_list.append({
                "name": name,
                "role": agent.role,
                "capabilities": agent.definition.capabilities,
                "created_at": agent.definition.created_at,
                "created_by": agent.definition.created_by
            })
        return sorted(agents_list, key=lambda x: x["created_at"])
    
    def delete_agent(self, name: str) -> bool:
        """Elimina un agente"""
        if name not in self._agents:
            return False
        
        # Eliminar de memoria
        del self._agents[name]
        
        # Eliminar archivo
        if name in self._manifest.get("agents", {}):
            agent_file = Path(self._manifest["agents"][name]["path"])
            if agent_file.exists():
                agent_file.unlink()
            del self._manifest["agents"][name]
            self._save_manifest()
        
        return True
    
    def call_agent(self, name: str, task: str, context: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Llama a un agente específico con una tarea.
        
        Returns:
            Dict con 'ok', 'response', 'agent_name', 'agent_role'
        """
        agent = self.get_agent(name)
        
        if not agent:
            return {
                "ok": False,
                "error": f"Agente '{name}' no encontrado",
                "available_agents": list(self._agents.keys())
            }
        
        try:
            print(f"\n[✨ LLAMANDO AGENTE] {agent.name} - {agent.role}")
            print(f"[AGENTE INFO] Creado: {agent.definition.created_at}")
            print(f"[AGENTE INFO] System Prompt: {agent.definition.system_prompt[:150]}...")
            
            response = agent.step(task, context)
            
            print(f"[✅ AGENTE RESPONDIÓ] Longitud: {len(response)} caracteres\n")
            
            return {
                "ok": True,
                "response": response,
                "agent_name": agent.name,
                "agent_role": agent.role,
                "system_prompt_preview": agent.definition.system_prompt[:100]
            }
        except Exception as e:
            import traceback
            print(f"[❌ ERROR EN AGENTE] {str(e)}")
            print(traceback.format_exc())
            return {
                "ok": False,
                "error": f"Error al ejecutar agente: {str(e)}",
                "agent_name": agent.name,
                "traceback": traceback.format_exc(limit=3)
            }
