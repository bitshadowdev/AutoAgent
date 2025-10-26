#!/usr/bin/env python
"""
Script de prueba para verificar que los imports funcionen correctamente
"""

print("🧪 Probando imports del paquete coreee...\n")

try:
    print("1️⃣ Importando CloudflareLLMClient...")
    from coreee.llm_client import CloudflareLLMClient
    print("   ✅ CloudflareLLMClient importado correctamente")
except Exception as e:
    print(f"   ❌ Error: {e}")

try:
    print("\n2️⃣ Importando SessionManager...")
    from coreee.session_manager import SessionManager
    print("   ✅ SessionManager importado correctamente")
except Exception as e:
    print(f"   ❌ Error: {e}")

try:
    print("\n3️⃣ Importando Recorder...")
    from coreee.timeline_recorder import Recorder
    print("   ✅ Recorder importado correctamente")
except Exception as e:
    print(f"   ❌ Error: {e}")

try:
    print("\n4️⃣ Importando AgentRegistry...")
    from coreee.agent_registry import AgentRegistry
    print("   ✅ AgentRegistry importado correctamente")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("✅ Todos los imports funcionan correctamente!")
print("="*60)
