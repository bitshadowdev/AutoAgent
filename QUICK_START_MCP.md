# Quick Start - Integración MCP

Guía rápida para empezar a usar servidores MCP con AutoAgent.

## 🚀 Instalación en 3 Pasos

### 1. Instalar el cliente MCP
```bash
pip install mcp
```

### 2. Verificar instalación
```bash
python test_mcp_integration.py
```

Deberías ver:
```
✅ PASS - MCP Package
✅ PASS - MCP Bridge Import
✅ PASS - Demo Server
✅ PASS - ToolRegistry
```

### 3. Configurar servidor demo
**Windows PowerShell:**
```powershell
$env:MCP_STDIO='[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]'
```

**Linux/Mac:**
```bash
export MCP_STDIO='[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]'
```

## 🎯 Probar la Integración

### Listar tools disponibles (incluye MCP)
```bash
python coreee/sistema_agentes_supervisor_coder.py --tools-list
```

Deberías ver las tools del servidor demo:
```
Tools persistentes en .permanent_tools
 - demo:calculate
 - demo:count_words
 - demo:generate_uuid
 - demo:get_current_time
 - demo:reverse_text
```

### Ejecutar una tarea usando MCP
```bash
python coreee/sistema_agentes_supervisor_coder.py -q "Calcula 25 * 4 usando la calculadora"
```

El Coder automáticamente:
1. Descubre la tool `demo:calculate`
2. La llama con `operation="multiply", a=25, b=4`
3. Retorna el resultado: `100`

### Más ejemplos de tareas

**Análisis de texto:**
```bash
python coreee/sistema_agentes_supervisor_coder.py -q "¿Cuántas palabras tiene 'Hola mundo desde MCP'?"
```

**Invertir texto:**
```bash
python coreee/sistema_agentes_supervisor_coder.py -q "Invierte el texto 'AutoAgent con MCP'"
```

**Obtener hora actual:**
```bash
python coreee/sistema_agentes_supervisor_coder.py -q "¿Qué hora es ahora en formato simple?"
```

## 📚 Documentación Completa

- **Guía completa**: [docs/MCP_INTEGRATION.md](docs/MCP_INTEGRATION.md)
- **Ejemplos**: [examples/README.md](examples/README.md)
- **Test de integración**: `python test_mcp_integration.py`

## 🔧 Troubleshooting Rápido

### Error: "No module named 'mcp'"
**Solución:**
```bash
pip install mcp
```

### Error: "Servidor no se conecta"
**Verificar:**
1. Variable `MCP_STDIO` está configurada correctamente (JSON válido)
2. Ruta al servidor es correcta
3. El servidor es ejecutable con Python

**Debug:**
```bash
# Probar servidor de forma aislada
python examples/mcp_server_demo.py
```

### Tools MCP no aparecen en listado
**Causas comunes:**
1. `MCP_STDIO` no está configurada en la sesión actual
2. Error de sintaxis en el JSON de configuración
3. Servidor tiene error al iniciar

**Revisar logs:**
```bash
python coreee/sistema_agentes_supervisor_coder.py -q "test" 2>&1 | findstr /i mcp
```

## 🎓 Próximos Pasos

1. **Crear tu propio servidor MCP** - Ver [docs/MCP_INTEGRATION.md#crear-tu-propio-servidor-mcp](docs/MCP_INTEGRATION.md#crear-tu-propio-servidor-mcp)
2. **Conectar múltiples servidores** - Añade más objetos al array de `MCP_STDIO`
3. **Filtrar tools con allow_list** - Controla qué tools están disponibles
4. **Revisar telemetría** - Ver métricas de performance de tools MCP en el timeline

## 💡 Tips

- Las tools MCP se llaman igual que las locales: `call_tool` con `name="server:tool"`
- El Supervisor no distingue entre tools locales y MCP
- Todas las métricas (latencia, errores, scoring) funcionan igual
- Los timeouts protegen contra tools que cuelgan
- Tools MCP aparecen en el manifest con `source: "mcp"`

---

**¿Preguntas?** Revisa [docs/MCP_INTEGRATION.md](docs/MCP_INTEGRATION.md) o abre un issue.
