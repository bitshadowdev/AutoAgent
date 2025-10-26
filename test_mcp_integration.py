#!/usr/bin/env python3
"""
Script de prueba para verificar la integración MCP.

Ejecutar:
    python test_mcp_integration.py
"""

import os
import sys
import json
from pathlib import Path

# Agregar coreee al path
sys.path.insert(0, str(Path(__file__).parent))

def test_mcp_package():
    """Verifica que el paquete MCP está instalado."""
    print("🔍 Verificando instalación de MCP...")
    try:
        import mcp
        print("✅ Paquete 'mcp' instalado correctamente")
        return True
    except ImportError:
        print("❌ Paquete 'mcp' NO instalado")
        print("   Instálalo con: pip install mcp")
        return False


def test_mcp_bridge_import():
    """Verifica que el módulo mcp_bridge se puede importar."""
    print("\n🔍 Verificando módulo mcp_bridge...")
    try:
        from coreee.mcp_bridge import MCPToolBridge, connect_mcp_servers_from_env
        print("✅ Módulo mcp_bridge importado correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error importando mcp_bridge: {e}")
        return False


def test_demo_server_exists():
    """Verifica que el servidor demo existe."""
    print("\n🔍 Verificando servidor demo...")
    demo_path = Path(__file__).parent / "examples" / "mcp_server_demo.py"
    if demo_path.exists():
        print(f"✅ Servidor demo encontrado: {demo_path}")
        return True
    else:
        print(f"❌ Servidor demo NO encontrado: {demo_path}")
        return False


def test_tool_registry():
    """Verifica que ToolRegistry tiene el método register_callable."""
    print("\n🔍 Verificando ToolRegistry...")
    try:
        from coreee.sistema_agentes_supervisor_coder import ToolRegistry
        registry = ToolRegistry()
        
        # Verificar que el método existe
        if not hasattr(registry, 'register_callable'):
            print("❌ ToolRegistry NO tiene método 'register_callable'")
            return False
        
        # Probar registrar un callable de prueba
        def test_fn(args):
            return {"ok": True, "test": "success"}
        
        registry.register_callable("test:callable", test_fn, source="test")
        
        # Verificar que se registró
        if registry.has("test:callable"):
            print("✅ ToolRegistry.register_callable funciona correctamente")
            return True
        else:
            print("❌ Tool no se registró correctamente")
            return False
            
    except Exception as e:
        print(f"❌ Error probando ToolRegistry: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_config_env():
    """Verifica la configuración MCP desde env."""
    print("\n🔍 Verificando configuración MCP_STDIO...")
    
    mcp_config = os.environ.get("MCP_STDIO")
    if not mcp_config:
        print("⚠️  Variable MCP_STDIO no está configurada")
        print("   Esto es opcional. Para probar MCP, configúrala así:")
        print('   $env:MCP_STDIO=\'[{"name":"demo","cmd":"python","args":["examples/mcp_server_demo.py"]}]\'')
        return None
    
    try:
        config = json.loads(mcp_config)
        print(f"✅ Configuración MCP válida: {len(config)} servidor(es)")
        for server in config:
            print(f"   - {server.get('name', 'unknown')}: {server.get('cmd')} {' '.join(server.get('args', []))}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Configuración MCP inválida (JSON): {e}")
        return False


def test_mcp_connection():
    """Intenta conectar a servidores MCP si están configurados."""
    print("\n🔍 Probando conexión a servidores MCP...")
    
    if not os.environ.get("MCP_STDIO"):
        print("⏭️  Saltando (MCP_STDIO no configurado)")
        return None
    
    try:
        from coreee.llm_client import CloudflareLLMClient
        from coreee.sistema_agentes_supervisor_coder import MiniAgentSystem
        
        # Crear sistema (esto debería autoconectar MCP)
        llm = CloudflareLLMClient()
        system = MiniAgentSystem(llm, recorder=None)
        
        # Verificar si hay tools MCP
        all_tools = system.tools.list()
        mcp_tools = [t for t in all_tools if ':' in t]
        
        if mcp_tools:
            print(f"✅ {len(mcp_tools)} tool(s) MCP registrada(s):")
            for tool in mcp_tools[:10]:  # Mostrar max 10
                print(f"   - {tool}")
            if len(mcp_tools) > 10:
                print(f"   ... y {len(mcp_tools) - 10} más")
            return True
        else:
            print("⚠️  No se encontraron tools MCP (puede ser normal si el servidor no tiene tools)")
            return None
            
    except Exception as e:
        print(f"❌ Error conectando a MCP: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta todas las pruebas."""
    print("=" * 60)
    print("🧪 TEST DE INTEGRACIÓN MCP")
    print("=" * 60)
    
    results = {
        "MCP Package": test_mcp_package(),
        "MCP Bridge Import": test_mcp_bridge_import(),
        "Demo Server": test_demo_server_exists(),
        "ToolRegistry": test_tool_registry(),
        "MCP Config": test_mcp_config_env(),
        "MCP Connection": test_mcp_connection(),
    }
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⏭️  SKIP"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed > 0:
        print("\n⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")
        return 1
    elif passed == 0:
        print("\n⚠️  No se pudo ejecutar ninguna prueba exitosamente.")
        return 1
    else:
        print("\n✅ Integración MCP lista para usar!")
        print("\nPróximos pasos:")
        print("1. Instalar MCP si no lo hiciste: pip install mcp")
        print("2. Configurar MCP_STDIO con tu servidor")
        print("3. Ejecutar: python coreee/sistema_agentes_supervisor_coder.py --tools-list")
        return 0


if __name__ == "__main__":
    exit(main())
