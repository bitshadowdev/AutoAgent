# Ejemplos de AutoAgent

Este directorio contiene ejemplos y servidores de prueba para AutoAgent.

## Servidores MCP

### `mcp_server_demo.py`

Servidor MCP de demostración con 5 tools básicas:

- **get_current_time**: Obtiene hora actual en varios formatos
- **calculate**: Operaciones matemáticas (suma, resta, multiplicación, división, potencia)
- **reverse_text**: Invierte cadenas de texto
- **count_words**: Analiza texto (palabras, caracteres, líneas)
- **generate_uuid**: Genera UUIDs aleatorios

#### Uso rápido

**1. Instalar MCP:**
```bash
pip install mcp
```

**2. Probar el servidor de forma aislada:**
```bash
python examples/mcp_server_demo.py
```

**3. Usar con AutoAgent:**

```powershell
# Windows PowerShell
$env:MCP_STDIO='[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]'
python coreee/sistema_agentes_supervisor_coder.py --tools-list
```

```bash
# Linux/Mac
export MCP_STDIO='[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]'
python coreee/sistema_agentes_supervisor_coder.py --tools-list
```

**4. Ejecutar una tarea:**
```bash
python coreee/sistema_agentes_supervisor_coder.py -q "Calcula 15 * 7 usando la tool de MCP"
```

## Documentación Completa

Ver [docs/MCP_INTEGRATION.md](../docs/MCP_INTEGRATION.md) para documentación completa sobre:
- Arquitectura de la integración MCP
- Configuración avanzada
- Crear tus propios servidores MCP
- Troubleshooting
- Mejores prácticas
