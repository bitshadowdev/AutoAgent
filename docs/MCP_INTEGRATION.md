# Integración MCP (Model Context Protocol)

AutoAgent ahora soporta la integración con servidores MCP, permitiendo que el Coder acceda a herramientas externas de forma transparente.

## ¿Qué es MCP?

El **Model Context Protocol (MCP)** es un estándar abierto para conectar modelos de IA con herramientas y servicios externos. Los servidores MCP exponen herramientas que pueden ser descubiertas y llamadas dinámicamente.

## Arquitectura de la Integración

```
┌─────────────────────────────────────────────────────────┐
│                   MiniAgentSystem                        │
│                                                          │
│  ┌──────────────┐      ┌───────────────┐               │
│  │  Supervisor  │◄────►│    Coder      │               │
│  └──────────────┘      └───────┬───────┘               │
│                                 │                        │
│                                 ▼                        │
│                        ┌────────────────┐               │
│                        │  ToolRegistry  │               │
│                        │                │               │
│                        │  ┌──────────┐  │               │
│                        │  │  Local   │  │               │
│                        │  │  Tools   │  │               │
│                        │  └──────────┘  │               │
│                        │                │               │
│                        │  ┌──────────┐  │               │
│                        │  │   MCP    │  │ ◄─────────────┤
│                        │  │  Tools   │  │               │
│                        │  └──────────┘  │               │
│                        └────────────────┘               │
└─────────────────────────────────────────────────────────┘
                                 ▲
                                 │ stdio
                                 │
                  ┌──────────────┴──────────────┐
                  │                             │
           ┌──────┴──────┐            ┌─────────┴────────┐
           │ MCP Server  │            │  MCP Server      │
           │   "demo"    │            │  "weather"       │
           │             │            │                  │
           │ - get_time  │            │ - get_forecast   │
           │ - calculate │            │ - get_current    │
           └─────────────┘            └──────────────────┘
```

## Características Clave

✅ **Descubrimiento automático**: Las tools MCP se registran automáticamente al inicio  
✅ **Sin cambios en el flujo**: El Supervisor y Coder funcionan igual  
✅ **Namespacing**: Tools MCP usan formato `servidor:tool` (ej: `demo:calculate`)  
✅ **Telemetría integrada**: Métricas, errores y scoring como tools locales  
✅ **Timeouts**: Protección contra tools MCP que cuelgan  
✅ **Manejo de errores**: Errores MCP se reportan con diagnósticos  

## Instalación

### 1. Instalar el cliente MCP

```bash
pip install mcp
```

### 2. Verificar instalación

```bash
python -c "import mcp; print('MCP instalado correctamente')"
```

## Configuración

### Formato de configuración

La conexión a servidores MCP se configura mediante la variable de entorno `MCP_STDIO` en formato JSON:

```json
[
  {
    "name": "demo",
    "cmd": "python",
    "args": ["examples/mcp_server_demo.py"],
    "env": {},
    "allow_list": null,
    "timeout": 30.0
  },
  {
    "name": "weather",
    "cmd": "node",
    "args": ["path/to/weather-server.js"],
    "env": {
      "API_KEY": "your-api-key-here"
    },
    "allow_list": ["get_*", "list_*"],
    "timeout": 15.0
  }
]
```

### Parámetros de configuración

- **`name`** (requerido): Identificador del servidor. Las tools se nombrarán `name:tool_name`
- **`cmd`** (requerido): Comando para ejecutar el servidor (ej: `python`, `node`, `./binary`)
- **`args`** (opcional): Lista de argumentos para el comando
- **`env`** (opcional): Variables de entorno adicionales para el servidor
- **`allow_list`** (opcional): Lista de patrones glob de tools permitidas. Si es `null`, se permiten todas
- **`timeout`** (opcional): Timeout en segundos para conexión y ejecución de tools (default: 30)

### Ejemplo de configuración completa

**Windows (PowerShell):**
```powershell
$env:MCP_STDIO='[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]'
```

**Linux/Mac (bash):**
```bash
export MCP_STDIO='[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]'
```

**Archivo .env:**
```
MCP_STDIO=[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]
```

## Uso

### 1. Iniciar AutoAgent con MCP

```bash
# Configurar variable de entorno
$env:MCP_STDIO='[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]'

# Listar todas las tools (incluye las de MCP)
python coreee/sistema_agentes_supervisor_coder.py --tools-list
```

Salida esperada:
```
Tools persistentes en .permanent_tools
 - demo:calculate
 - demo:count_words
 - demo:generate_uuid
 - demo:get_current_time
 - demo:reverse_text
 - mi_tool_local
```

### 2. Usar tools MCP desde el Coder

El Coder puede llamar tools MCP igual que tools locales:

**Llamada directa:**
```json
{
  "type": "call_tool",
  "message": "Voy a calcular la suma",
  "call": {
    "name": "demo:calculate",
    "args": {
      "operation": "add",
      "a": 10,
      "b": 5
    }
  }
}
```

**El Supervisor no necesita cambios** - sigue decidiendo `end` o `coder` basándose en resultados.

### 3. Ejecutar tarea usando MCP

```bash
python coreee/sistema_agentes_supervisor_coder.py -q "¿Cuántas palabras tiene el texto 'Hola mundo desde MCP'?"
```

El sistema automáticamente:
1. Conecta al servidor MCP `demo`
2. Descubre la tool `demo:count_words`
3. El Coder la llama con el texto
4. Retorna el resultado al usuario

## Servidor MCP de Ejemplo

El proyecto incluye un servidor de demostración en `examples/mcp_server_demo.py` con las siguientes tools:

### `demo:get_current_time`
Obtiene la hora actual del sistema.

**Args:**
- `format` (string, opcional): Formato de salida - `"iso"`, `"simple"`, o `"timestamp"`

**Ejemplo:**
```json
{"format": "simple"}
```

**Respuesta:**
```json
{
  "time": "2025-10-26 14:30:00",
  "format": "simple",
  "timezone": "local"
}
```

### `demo:calculate`
Realiza operaciones matemáticas.

**Args:**
- `operation` (string): Operación - `"add"`, `"subtract"`, `"multiply"`, `"divide"`, `"power"`
- `a` (number): Primer número
- `b` (number): Segundo número

**Ejemplo:**
```json
{
  "operation": "multiply",
  "a": 7,
  "b": 6
}
```

**Respuesta:**
```json
{
  "result": 42,
  "operation": "multiply",
  "a": 7,
  "b": 6,
  "ok": true
}
```

### `demo:reverse_text`
Invierte una cadena de texto.

**Args:**
- `text` (string): Texto a invertir

**Ejemplo:**
```json
{"text": "Hola Mundo"}
```

**Respuesta:**
```json
{
  "original": "Hola Mundo",
  "reversed": "odnuM aloH",
  "length": 10,
  "ok": true
}
```

### `demo:count_words`
Cuenta palabras, caracteres y líneas en un texto.

**Args:**
- `text` (string): Texto a analizar

**Ejemplo:**
```json
{"text": "Hola mundo\nDesde MCP"}
```

**Respuesta:**
```json
{
  "text": "Hola mundo\nDesde MCP",
  "word_count": 4,
  "char_count": 19,
  "line_count": 2,
  "ok": true
}
```

### `demo:generate_uuid`
Genera un UUID v4 aleatorio.

**Args:** (ninguno)

**Respuesta:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "version": 4,
  "ok": true
}
```

## Crear tu Propio Servidor MCP

### Estructura básica

```python
#!/usr/bin/env python3
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("mi-servidor")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="mi_tool",
            description="Descripción de mi tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Descripción del parámetro"
                    }
                },
                "required": ["param1"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "mi_tool":
        result = {"ok": True, "data": "resultado"}
        return [TextContent(
            type="text",
            text=json.dumps(result)
        )]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### Registrar el servidor

```powershell
$env:MCP_STDIO='[{"name":"miserver","cmd":"python","args":["path/to/mi_servidor.py"]}]'
```

## Debugging y Troubleshooting

### Ver logs de conexión MCP

Los eventos MCP se registran en el timeline:

```bash
python coreee/sistema_agentes_supervisor_coder.py -q "tu tarea"

# Revisar el archivo de eventos
cat .runs/YYYY-MM-DD_HH-MM-SS/events.jsonl | grep mcp
```

### Tipos de eventos MCP

- **`mcp_connected`**: Servidores conectados exitosamente
- **`mcp_error`**: Error conectando o ejecutando tool
- **`mcp_unavailable`**: Paquete `mcp` no instalado
- **`mcp_timeout`**: Tool MCP excedió el timeout

### Errores comunes

#### ImportError: No module named 'mcp'
**Solución:**
```bash
pip install mcp
```

#### Timeout conectando al servidor
**Causa**: El servidor tarda mucho en iniciar  
**Solución**: Aumentar el `timeout` en la configuración:
```json
{"name":"demo","cmd":"python","args":["server.py"],"timeout":60.0}
```

#### Tool MCP no aparece en listado
**Causas posibles:**
1. El servidor no está en `MCP_STDIO`
2. La tool está filtrada por `allow_list`
3. Error en el servidor (revisar logs)

**Solución**: Revisar el timeline para errores:
```bash
cat .runs/*/events.jsonl | grep -i error
```

#### Division por cero u otros errores de tool
**Comportamiento**: El error se reporta como cualquier tool local  
**El Supervisor**: Detecta el error y pide corrección al Coder  
**No requiere intervención manual**

## Mejores Prácticas

### 1. Naming de servidores
- Usa nombres descriptivos y cortos: `weather`, `db`, `api`
- Evita caracteres especiales (solo letras, números, guiones)

### 2. Seguridad
- **No expongas API keys** en la config pública
- Usa variables de entorno para secretos:
  ```json
  {"name":"api","cmd":"python","args":["server.py"],"env":{"API_KEY":"${API_KEY}"}}
  ```
- Usa `allow_list` para limitar tools disponibles

### 3. Performance
- Configura timeouts razonables (15-30s)
- Tools lentas deben avisar progreso
- Cachea resultados cuando sea posible

### 4. Manejo de errores
- Siempre retorna `{"ok": true/false}` en el JSON de respuesta
- Incluye mensajes de error descriptivos
- Usa códigos de error consistentes

### 5. Testing
- Prueba tu servidor MCP de forma aislada antes de integrarlo
- Verifica el esquema JSON de inputs
- Testea casos límite y errores

## Integración con Otros Componentes

### Timeline/Recorder
- Todas las llamadas a tools MCP se registran
- Métricas de latencia y éxito/error
- Scoring automático igual que tools locales

### Session Manager
- Tools MCP usadas se persisten en `tools_used`
- Estadísticas en `custom_data.tool_stats`

### Telemetría
- Latencia promedio por tool MCP
- Tasa de éxito/error
- Score automático basado en performance

## Roadmap Futuro

- [ ] Soporte para MCP HTTP (además de stdio)
- [ ] Cache de resultados de tools MCP
- [ ] Hot-reload de servidores MCP
- [ ] UI para gestionar servidores MCP
- [ ] Validación de schemas de input
- [ ] Retry automático para tools que fallan

## Referencias

- [Especificación MCP](https://modelcontextprotocol.io/)
- [SDK Python MCP](https://github.com/modelcontextprotocol/python-sdk)
- [Ejemplos de servidores MCP](https://github.com/modelcontextprotocol/servers)

## Soporte

Para problemas o preguntas sobre la integración MCP, abre un issue en el repositorio con:
- Variable `MCP_STDIO` (sin API keys)
- Logs del timeline (`.runs/*/events.jsonl`)
- Versión de `mcp` (`pip show mcp`)
