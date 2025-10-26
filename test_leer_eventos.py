#!/usr/bin/env python3
"""Script para verificar que los eventos tienen el código de las herramientas."""

from coreee.event_logger import EventLogger
from pathlib import Path

# Leer eventos de la sesión más reciente
runs_dir = Path(".runs")
if runs_dir.exists():
    run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    if run_dirs:
        latest_events = run_dirs[0] / "events.jsonl"
        print(f"📁 Leyendo: {latest_events}\n")
        
        events = EventLogger.read_events(str(latest_events))
        
        # Filtrar eventos de herramientas
        tool_events = [e for e in events if e.etype in ["tool_create", "tool_update"]]
        
        print(f"🔍 Encontrados {len(tool_events)} eventos de herramientas\n")
        
        for event in tool_events:
            tool_name = event.data.get("tool_name", "N/A")
            code = event.data.get("code", "")
            code_path = event.data.get("code_path", "N/A")
            
            print(f"{'='*60}")
            print(f"🔧 Herramienta: {tool_name}")
            print(f"   Tipo: {event.etype}")
            print(f"   Turno: {event.turn}")
            print(f"   Code path: {code_path}")
            print(f"   ¿Tiene código? {'✅ SÍ' if code else '❌ NO'}")
            
            if code:
                lines = code.count('\n') + 1
                chars = len(code)
                print(f"   Líneas: {lines}")
                print(f"   Caracteres: {chars}")
                print(f"\n   Primeras 3 líneas:")
                for i, line in enumerate(code.split('\n')[:3], 1):
                    print(f"     {i:2d}  {line}")
            else:
                print(f"   ⚠️ Código no está en data.code")
                # Intentar leer del archivo
                if code_path != "N/A":
                    cp = Path(code_path)
                    if cp.exists():
                        print(f"   ✅ Pero el archivo existe: {cp}")
                        code_from_file = cp.read_text(encoding='utf-8')
                        print(f"   Líneas en archivo: {code_from_file.count(chr(10)) + 1}")
                    else:
                        print(f"   ❌ El archivo no existe: {cp}")
            
            print()
    else:
        print("❌ No hay directorios en .runs/")
else:
    print("❌ Directorio .runs/ no existe")
