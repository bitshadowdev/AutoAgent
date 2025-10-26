#!/usr/bin/env python3
"""
Servidor MCP de demostración con tools de ejemplo.

Este servidor implementa el protocolo MCP (Model Context Protocol) y expone
varias herramientas de ejemplo que pueden ser consumidas por AutoAgent.

Para ejecutar:
    python examples/mcp_server_demo.py

Para usar con AutoAgent, configura la variable de entorno:
    MCP_STDIO='[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]'
    
Requiere:
    pip install mcp
"""

import asyncio
import json
from datetime import datetime
from typing import Any

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("ERROR: El paquete 'mcp' no está instalado.")
    print("Instálalo con: pip install mcp")
    exit(1)


# Crear servidor MCP
app = Server("demo-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista las tools disponibles en este servidor."""
    return [
        Tool(
            name="get_current_time",
            description="Obtiene la hora actual del sistema",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "Formato de fecha (iso, simple, timestamp)",
                        "enum": ["iso", "simple", "timestamp"],
                        "default": "iso"
                    }
                }
            }
        ),
        Tool(
            name="calculate",
            description="Realiza cálculos matemáticos simples",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "Operación a realizar",
                        "enum": ["add", "subtract", "multiply", "divide", "power"]
                    },
                    "a": {
                        "type": "number",
                        "description": "Primer número"
                    },
                    "b": {
                        "type": "number",
                        "description": "Segundo número"
                    }
                },
                "required": ["operation", "a", "b"]
            }
        ),
        Tool(
            name="reverse_text",
            description="Invierte una cadena de texto",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Texto a invertir"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="count_words",
            description="Cuenta palabras en un texto",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Texto a analizar"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="generate_uuid",
            description="Genera un UUID v4 aleatorio",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Ejecuta una tool según su nombre."""
    
    if name == "get_current_time":
        fmt = arguments.get("format", "iso")
        now = datetime.now()
        
        if fmt == "iso":
            result = now.isoformat()
        elif fmt == "simple":
            result = now.strftime("%Y-%m-%d %H:%M:%S")
        elif fmt == "timestamp":
            result = str(int(now.timestamp()))
        else:
            result = now.isoformat()
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "time": result,
                "format": fmt,
                "timezone": "local"
            })
        )]
    
    elif name == "calculate":
        op = arguments.get("operation")
        a = float(arguments.get("a", 0))
        b = float(arguments.get("b", 0))
        
        operations = {
            "add": a + b,
            "subtract": a - b,
            "multiply": a * b,
            "divide": a / b if b != 0 else None,
            "power": a ** b
        }
        
        result = operations.get(op)
        
        if result is None and op == "divide":
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "División por cero",
                    "ok": False
                })
            )]
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "result": result,
                "operation": op,
                "a": a,
                "b": b,
                "ok": True
            })
        )]
    
    elif name == "reverse_text":
        text = arguments.get("text", "")
        reversed_text = text[::-1]
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "original": text,
                "reversed": reversed_text,
                "length": len(text),
                "ok": True
            })
        )]
    
    elif name == "count_words":
        text = arguments.get("text", "")
        words = text.split()
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "text": text[:100] + ("..." if len(text) > 100 else ""),
                "word_count": len(words),
                "char_count": len(text),
                "line_count": len(text.splitlines()),
                "ok": True
            })
        )]
    
    elif name == "generate_uuid":
        import uuid
        generated = str(uuid.uuid4())
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "uuid": generated,
                "version": 4,
                "ok": True
            })
        )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Tool desconocida: {name}",
                "ok": False
            })
        )]


async def main():
    """Ejecuta el servidor MCP por stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    print("🚀 Servidor MCP Demo iniciando...", flush=True)
    asyncio.run(main())
