# Script de setup para integración MCP en AutoAgent
# Ejecutar: .\setup_mcp.ps1

Write-Host "🚀 Setup de Integración MCP para AutoAgent" -ForegroundColor Cyan
Write-Host "=" * 60

# 1. Verificar Python
Write-Host "`n📍 Paso 1: Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python instalado: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python no encontrado. Instala Python 3.9+ primero." -ForegroundColor Red
    exit 1
}

# 2. Instalar paquete MCP
Write-Host "`n📍 Paso 2: Instalando paquete 'mcp'..." -ForegroundColor Yellow
Write-Host "Ejecutando: pip install mcp`n"
pip install mcp

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Paquete 'mcp' instalado correctamente" -ForegroundColor Green
} else {
    Write-Host "❌ Error instalando 'mcp'. Verifica tu conexión a internet." -ForegroundColor Red
    exit 1
}

# 3. Ejecutar tests
Write-Host "`n📍 Paso 3: Ejecutando tests de integración..." -ForegroundColor Yellow
python test_mcp_integration.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Tests pasaron correctamente" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Algunos tests fallaron. Revisa los errores arriba." -ForegroundColor Yellow
}

# 4. Configurar variable de entorno
Write-Host "`n📍 Paso 4: Configurando servidor MCP demo..." -ForegroundColor Yellow

$currentDir = Get-Location
$configJson = @"
[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]
"@

Write-Host "Configurando MCP_STDIO en la sesión actual..."
$env:MCP_STDIO = $configJson

Write-Host "✅ Variable MCP_STDIO configurada para esta sesión" -ForegroundColor Green
Write-Host "`n📋 Valor configurado:"
Write-Host $configJson -ForegroundColor Gray

# 5. Listar tools
Write-Host "`n📍 Paso 5: Listando tools disponibles (incluyendo MCP)..." -ForegroundColor Yellow
Write-Host "Ejecutando: python coreee/sistema_agentes_supervisor_coder.py --tools-list`n"
python coreee/sistema_agentes_supervisor_coder.py --tools-list

# 6. Instrucciones finales
Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "✅ SETUP COMPLETADO" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Cyan

Write-Host "`n📚 Próximos pasos:" -ForegroundColor Yellow
Write-Host "1. Probar una tarea con MCP:"
Write-Host '   python coreee/sistema_agentes_supervisor_coder.py -q "Calcula 25 * 4"' -ForegroundColor Gray
Write-Host "`n2. Ver documentación completa:"
Write-Host "   - QUICK_START_MCP.md" -ForegroundColor Gray
Write-Host "   - docs/MCP_INTEGRATION.md" -ForegroundColor Gray
Write-Host "`n3. Crear tu propio servidor MCP:"
Write-Host "   Ver ejemplos en: examples/mcp_server_demo.py" -ForegroundColor Gray

Write-Host "`n⚠️  NOTA IMPORTANTE:" -ForegroundColor Yellow
Write-Host "La variable MCP_STDIO solo está configurada para esta sesión de PowerShell."
Write-Host "Para hacerla permanente, agrégala a tu perfil o usa un archivo .env"
Write-Host "`nPara configurarla en cada sesión, ejecuta:"
Write-Host '$env:MCP_STDIO=''[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]''' -ForegroundColor Gray

Write-Host "`n🎉 ¡Listo para usar AutoAgent con MCP!" -ForegroundColor Green
