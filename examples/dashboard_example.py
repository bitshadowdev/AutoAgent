"""
Ejemplo de uso del Dashboard en Tiempo Real.

Este script muestra cómo:
1. Usar EnhancedRecorder para emitir eventos
2. Los eventos aparecen automáticamente en el dashboard
3. Crear listeners personalizados para eventos

Para probar:
    # Terminal 1: Iniciar dashboard
    streamlit run dashboard_streamlit.py
    
    # Terminal 2: Ejecutar este ejemplo
    python examples/dashboard_example.py
"""

import sys
import time
from pathlib import Path

# Agregar coreee al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from coreee.enhanced_recorder import create_recorder
from coreee.event_bus import get_event_bus, SystemEvent


def custom_listener(event: SystemEvent):
    """Listener personalizado que imprime eventos en consola."""
    print(f"[LISTENER] {event.role.upper():10s} | {event.etype:20s} | {event.summary[:50]}")


def main():
    print("=" * 70)
    print("📊 Ejemplo de Dashboard en Tiempo Real")
    print("=" * 70)
    print("\n💡 Asegúrate de tener el dashboard corriendo:")
    print("   streamlit run dashboard_streamlit.py")
    print("\n🔄 Emitiendo eventos en 3 segundos...\n")
    time.sleep(3)
    
    # Obtener EventBus y suscribir listener
    bus = get_event_bus()
    bus.subscribe(custom_listener)
    
    # Crear recorder
    recorder = create_recorder(
        root=".runs/dashboard_example",
        session_id="example_session",
        use_enhanced=True
    )
    
    print("🚀 Iniciando simulación de eventos...\n")
    
    # Evento 1: Inicio de sesión
    recorder.emit_session_start(turn=0, task="Ejemplo de visualización en tiempo real")
    time.sleep(1)
    
    # Evento 2: Mensaje de usuario
    recorder.emit_user_message(turn=1, content="Hola, quiero que crees una herramienta para calcular")
    time.sleep(1)
    
    # Evento 3: Respuesta del Coder
    recorder.emit_coder_message(
        turn=2,
        content="Voy a crear una herramienta llamada 'calculadora'",
        action="thinking"
    )
    time.sleep(1)
    
    # Evento 4: Creación de herramienta
    code = """def calculadora(args):
    a = args.get('a', 0)
    b = args.get('b', 0)
    op = args.get('operation', 'add')
    
    if op == 'add':
        return {'ok': True, 'result': a + b}
    elif op == 'subtract':
        return {'ok': True, 'result': a - b}
    elif op == 'multiply':
        return {'ok': True, 'result': a * b}
    elif op == 'divide':
        if b != 0:
            return {'ok': True, 'result': a / b}
        return {'ok': False, 'error': 'División por cero'}
    else:
        return {'ok': False, 'error': f'Operación desconocida: {op}'}
"""
    
    recorder.emit_tool_creation(
        turn=3,
        tool_name="calculadora",
        code=code,
        is_update=False
    )
    time.sleep(2)
    
    # Evento 5: Invocación de herramienta
    recorder.emit_tool_invocation(
        turn=4,
        tool_name="calculadora",
        args={"a": 10, "b": 5, "operation": "multiply"}
    )
    time.sleep(1)
    
    # Evento 6: Resultado de herramienta
    recorder.emit_tool_result(
        turn=4,
        tool_name="calculadora",
        result={"ok": True, "result": 50},
        success=True
    )
    time.sleep(1)
    
    # Evento 7: Mensaje del Coder con resultado
    recorder.emit_coder_message(
        turn=5,
        content="El resultado de 10 * 5 es 50",
        action="responding"
    )
    time.sleep(1)
    
    # Evento 8: Decisión del Supervisor
    recorder.emit(
        turn=6,
        role="supervisor",
        etype="supervisor_decision",
        summary="Decisión: continuar",
        data={
            "decision": "coder",
            "reasoning": "La herramienta fue creada exitosamente, continuar con la tarea"
        }
    )
    time.sleep(1)
    
    # Evento 9: Crear agente
    recorder.emit_agent_created(
        turn=7,
        agent_name="math_expert",
        role_desc="Experto en Matemáticas",
        capabilities=["cálculos", "álgebra", "geometría"]
    )
    time.sleep(1)
    
    # Evento 10: Invocar agente
    recorder.emit_agent_invocation(
        turn=8,
        agent_name="math_expert",
        task="Explica la operación de multiplicación"
    )
    time.sleep(1)
    
    # Evento 11: Respuesta de agente
    recorder.emit_agent_response(
        turn=8,
        agent_name="math_expert",
        response="La multiplicación es una operación matemática que consiste en sumar un número tantas veces como indica otro número..."
    )
    time.sleep(1)
    
    # Evento 12: Error simulado
    recorder.emit_error(
        turn=9,
        error_type="simulation",
        message="Este es un error de ejemplo (no es real)",
        traceback="Traceback (simulated):\n  File example.py, line 123\n    raise ValueError('Ejemplo')"
    )
    time.sleep(1)
    
    # Evento 13: Fin de sesión
    recorder.emit_session_end(
        turn=10,
        status="completed",
        summary="Ejemplo completado exitosamente"
    )
    
    print("\n" + "=" * 70)
    print("✅ Eventos emitidos completados!")
    print("=" * 70)
    print("\n📊 Revisa el dashboard en http://localhost:8501")
    print("\nDeberías ver:")
    print("  - Timeline con 13 eventos")
    print("  - Tab 'Mensajes' con la conversación")
    print("  - Tab 'Herramientas' con el código de la calculadora")
    print("  - Tab 'Estadísticas' con gráficos")
    print("  - Tab 'Inspector' con detalles de cada evento")
    print("\n💡 Puedes ejecutar este script múltiples veces")
    print("   Los eventos se acumularán en el dashboard")
    
    # Mostrar estadísticas
    stats = bus.get_stats()
    print("\n📈 Estadísticas del EventBus:")
    print(f"  - Total eventos en memoria: {stats['total_events']}")
    print(f"  - Listeners activos: {stats['total_listeners']}")
    print(f"  - Eventos por tipo:")
    for etype, count in sorted(stats['events_by_type'].items(), key=lambda x: -x[1])[:5]:
        print(f"    • {etype}: {count}")


if __name__ == "__main__":
    main()
