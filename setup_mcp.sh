#!/bin/bash
# Script de setup para integración MCP en AutoAgent
# Ejecutar: bash setup_mcp.sh

echo "🚀 Setup de Integración MCP para AutoAgent"
echo "============================================================"

# 1. Verificar Python
echo ""
echo "📍 Paso 1: Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python instalado: $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo "✅ Python instalado: $PYTHON_VERSION"
    PYTHON_CMD="python"
else
    echo "❌ Python no encontrado. Instala Python 3.9+ primero."
    exit 1
fi

# 2. Instalar paquete MCP
echo ""
echo "📍 Paso 2: Instalando paquete 'mcp'..."
echo "Ejecutando: pip install mcp"
echo ""
$PYTHON_CMD -m pip install mcp

if [ $? -eq 0 ]; then
    echo "✅ Paquete 'mcp' instalado correctamente"
else
    echo "❌ Error instalando 'mcp'. Verifica tu conexión a internet."
    exit 1
fi

# 3. Ejecutar tests
echo ""
echo "📍 Paso 3: Ejecutando tests de integración..."
$PYTHON_CMD test_mcp_integration.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Tests pasaron correctamente"
else
    echo ""
    echo "⚠️  Algunos tests fallaron. Revisa los errores arriba."
fi

# 4. Configurar variable de entorno
echo ""
echo "📍 Paso 4: Configurando servidor MCP demo..."

CONFIG_JSON='[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]'

echo "Configurando MCP_STDIO en la sesión actual..."
export MCP_STDIO="$CONFIG_JSON"

echo "✅ Variable MCP_STDIO configurada para esta sesión"
echo ""
echo "📋 Valor configurado:"
echo "$CONFIG_JSON"

# 5. Listar tools
echo ""
echo "📍 Paso 5: Listando tools disponibles (incluyendo MCP)..."
echo "Ejecutando: python coreee/sistema_agentes_supervisor_coder.py --tools-list"
echo ""
$PYTHON_CMD coreee/sistema_agentes_supervisor_coder.py --tools-list

# 6. Instrucciones finales
echo ""
echo "============================================================"
echo "✅ SETUP COMPLETADO"
echo "============================================================"

echo ""
echo "📚 Próximos pasos:"
echo "1. Probar una tarea con MCP:"
echo '   python coreee/sistema_agentes_supervisor_coder.py -q "Calcula 25 * 4"'
echo ""
echo "2. Ver documentación completa:"
echo "   - QUICK_START_MCP.md"
echo "   - docs/MCP_INTEGRATION.md"
echo ""
echo "3. Crear tu propio servidor MCP:"
echo "   Ver ejemplos en: examples/mcp_server_demo.py"

echo ""
echo "⚠️  NOTA IMPORTANTE:"
echo "La variable MCP_STDIO solo está configurada para esta sesión de terminal."
echo "Para hacerla permanente, agrégala a tu ~/.bashrc o ~/.zshrc:"
echo ""
echo 'export MCP_STDIO='"'"'[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]'"'"''

echo ""
echo "🎉 ¡Listo para usar AutoAgent con MCP!"
