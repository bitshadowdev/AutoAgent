"""
Bridge para conectar servidores MCP (Model Context Protocol) al ToolRegistry.

Conecta por stdio a servidores MCP, descubre sus tools y las registra como
callables externos en el ToolRegistry. Las tools MCP quedan invocables igual
que las tools locales, sin tocar el flujo del Supervisor/Coder.

Uso:
    bridge = MCPToolBridge(tool_registry)
    await bridge.connect_stdio(
        server_name="weather",
        command="python",
        args=["path/to/server_weather.py"]
    )
    # Ahora "weather:get_forecast" está disponible en tool_registry
    await bridge.aclose()

Requiere:
    pip install mcp
"""

import os
import asyncio
from typing import Dict, Callable, Any, Optional, List
from contextlib import AsyncExitStack

# SDK MCP (cliente stdio)
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None


class MCPToolBridge:
    """Bridge para integrar servidores MCP como tools en el ToolRegistry."""
    
    def __init__(self, registry) -> None:
        """
        Args:
            registry: Instancia de ToolRegistry donde se registrarán las tools MCP
        """
        if not MCP_AVAILABLE:
            raise ImportError(
                "El paquete 'mcp' no está instalado. "
                "Instálalo con: pip install mcp"
            )
        
        self.registry = registry
        self._exit = AsyncExitStack()
        self._sessions: Dict[str, ClientSession] = {}
        self._tool_to_server: Dict[str, str] = {}  # mapeo tool_fqn -> server_name

    async def connect_stdio(
        self, 
        server_name: str, 
        command: str, 
        args: Optional[List[str]] = None, 
        env: Optional[Dict[str, str]] = None,
        allow_list: Optional[List[str]] = None,
        timeout: float = 30.0
    ) -> int:
        """
        Lanza un server MCP por stdio y registra sus tools en el ToolRegistry.
        
        Args:
            server_name: Nombre identificador del servidor (ej: "weather")
            command: Comando para ejecutar el servidor (ej: "python", "node")
            args: Argumentos del comando (ej: ["server.py"])
            env: Variables de entorno adicionales para el servidor
            allow_list: Lista de prefijos de tools permitidas (ej: ["get_*", "list_*"])
                       Si es None, se permiten todas las tools del servidor
            timeout: Timeout en segundos para la conexión inicial
        
        Returns:
            Número de tools registradas desde este servidor
        
        Raises:
            TimeoutError: Si la conexión tarda más del timeout
            Exception: Si hay error conectando al servidor
        """
        params = StdioServerParameters(
            command=command, 
            args=args or [], 
            env=env or {}
        )
        
        try:
            # Conectar con timeout
            async with asyncio.timeout(timeout):
                stdio = await self._exit.enter_async_context(stdio_client(params))
                reader, writer = stdio
                session = await self._exit.enter_async_context(
                    ClientSession(reader, writer)
                )
                await session.initialize()
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Timeout conectando al servidor MCP '{server_name}' "
                f"después de {timeout}s"
            )
        except Exception as e:
            raise Exception(
                f"Error conectando al servidor MCP '{server_name}': {e}"
            )
        
        self._sessions[server_name] = session
        
        # Descubrir tools del servidor
        try:
            tool_list = await session.list_tools()
        except Exception as e:
            raise Exception(
                f"Error listando tools del servidor '{server_name}': {e}"
            )
        
        registered_count = 0
        for t in tool_list.tools:
            tool_fqn = f"{server_name}:{t.name}"
            
            # Filtrar por allow_list si se especificó
            if allow_list is not None:
                import fnmatch
                allowed = any(
                    fnmatch.fnmatch(t.name, pattern) 
                    for pattern in allow_list
                )
                if not allowed:
                    continue
            
            # Crear wrapper async que normaliza el resultado
            async def _run(
                _session: ClientSession, 
                _name: str, 
                _args: Dict[str, Any],
                _timeout: float = 30.0
            ) -> Dict[str, Any]:
                """Ejecuta una tool MCP con timeout."""
                try:
                    async with asyncio.timeout(_timeout):
                        res = await _session.call_tool(_name, _args or {})
                    # Normaliza a tu contrato: JSON-serializable
                    content = getattr(res, "content", None)
                    return {
                        "ok": True, 
                        "content": content,
                        "source": "mcp"
                    }
                except asyncio.TimeoutError:
                    return {
                        "ok": False,
                        "error": f"Timeout ejecutando tool MCP '{_name}' (>{_timeout}s)",
                        "code": "MCP_TIMEOUT",
                        "source": "mcp"
                    }
                except Exception as e:
                    return {
                        "ok": False,
                        "error": f"Error en tool MCP '{_name}': {str(e)}",
                        "code": "MCP_TOOL_ERROR",
                        "source": "mcp",
                        "traceback": str(e)
                    }
            
            # Wrapper sync para integrarse con ToolRegistry.call(...)
            # Captura las variables en el closure
            def _make_wrapper(_s, _n):
                def _wrapper(args: Dict[str, Any]) -> Dict[str, Any]:
                    """Wrapper sincrónico que ejecuta la tool MCP async."""
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Si ya hay un loop corriendo, crear una tarea
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(
                                    asyncio.run, 
                                    _run(_s, _n, args)
                                )
                                return future.result()
                        else:
                            # Si no hay loop, ejecutar normalmente
                            return loop.run_until_complete(_run(_s, _n, args))
                    except Exception as e:
                        return {
                            "ok": False,
                            "error": f"Error ejecutando wrapper MCP: {str(e)}",
                            "code": "MCP_WRAPPER_ERROR",
                            "source": "mcp"
                        }
                return _wrapper
            
            # Registrar la tool con metadata
            wrapper = _make_wrapper(session, t.name)
            self.registry.register_callable(
                tool_fqn, 
                wrapper, 
                source="mcp",
                meta={
                    "server": server_name,
                    "description": getattr(t, "description", ""),
                    "input_schema": getattr(t, "inputSchema", {})
                }
            )
            
            self._tool_to_server[tool_fqn] = server_name
            registered_count += 1
        
        return registered_count

    def get_connected_servers(self) -> List[str]:
        """Retorna lista de nombres de servidores MCP conectados."""
        return list(self._sessions.keys())
    
    def get_tools_from_server(self, server_name: str) -> List[str]:
        """Retorna lista de tools registradas desde un servidor específico."""
        return [
            tool for tool, srv in self._tool_to_server.items() 
            if srv == server_name
        ]

    async def aclose(self) -> None:
        """Cierra todas las conexiones a servidores MCP."""
        await self._exit.aclose()
        self._sessions.clear()
        self._tool_to_server.clear()


# Funciones de utilidad para uso simple
async def connect_mcp_servers_from_env(
    registry, 
    env_var: str = "MCP_STDIO"
) -> Dict[str, Any]:
    """
    Conecta servidores MCP desde variable de entorno JSON.
    
    Args:
        registry: ToolRegistry donde registrar las tools
        env_var: Nombre de la variable de entorno (default: "MCP_STDIO")
    
    Returns:
        Dict con estadísticas de conexión:
        {
            "servers_connected": int,
            "total_tools": int,
            "servers": [{"name": str, "tools": int}, ...],
            "errors": [{"server": str, "error": str}, ...]
        }
    
    Formato de la variable de entorno (JSON):
    [
        {
            "name": "weather",
            "cmd": "python",
            "args": ["path/to/server.py"],
            "env": {"API_KEY": "xxx"}  // opcional
        }
    ]
    """
    import json
    
    cfg = os.environ.get(env_var)
    if not cfg:
        return {
            "servers_connected": 0,
            "total_tools": 0,
            "servers": [],
            "errors": []
        }
    
    try:
        servers = json.loads(cfg)
    except json.JSONDecodeError as e:
        return {
            "servers_connected": 0,
            "total_tools": 0,
            "servers": [],
            "errors": [{"server": "config", "error": f"JSON inválido: {e}"}]
        }
    
    if not isinstance(servers, list):
        return {
            "servers_connected": 0,
            "total_tools": 0,
            "servers": [],
            "errors": [{"server": "config", "error": "Debe ser un array JSON"}]
        }
    
    bridge = MCPToolBridge(registry)
    stats = {
        "servers_connected": 0,
        "total_tools": 0,
        "servers": [],
        "errors": []
    }
    
    for s in servers:
        try:
            if not isinstance(s, dict) or "name" not in s or "cmd" not in s:
                stats["errors"].append({
                    "server": s.get("name", "unknown"),
                    "error": "Configuración inválida: requiere 'name' y 'cmd'"
                })
                continue
            
            count = await bridge.connect_stdio(
                server_name=s["name"],
                command=s["cmd"],
                args=s.get("args"),
                env=s.get("env"),
                allow_list=s.get("allow_list"),
                timeout=s.get("timeout", 30.0)
            )
            
            stats["servers_connected"] += 1
            stats["total_tools"] += count
            stats["servers"].append({
                "name": s["name"],
                "tools": count
            })
            
        except Exception as e:
            stats["errors"].append({
                "server": s.get("name", "unknown"),
                "error": str(e)
            })
    
    return stats
