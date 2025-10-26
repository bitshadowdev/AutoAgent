"""
Script para ejecutar AutoAgent con dashboard en tiempo real.

Este script:
1. Inicia el dashboard Streamlit en una ventana separada
2. Ejecuta el sistema AutoAgent con EnhancedRecorder
3. Todos los eventos se visualizan en tiempo real en el dashboard

Uso:
    python run_with_dashboard.py -q "tu tarea aquí"
    
O puedes ejecutar manualmente:
    # Terminal 1: Dashboard
    streamlit run dashboard_streamlit.py
    
    # Terminal 2: Sistema
    python run_with_dashboard.py -q "tu tarea"
"""

import subprocess
import sys
import time
import argparse
from pathlib import Path
import os

# Agregar coreee al path
sys.path.insert(0, str(Path(__file__).parent))


def start_dashboard():
    """Inicia el dashboard Streamlit en un proceso separado."""
    dashboard_path = Path(__file__).parent / "dashboard_streamlit.py"
    
    print("🚀 Iniciando dashboard Streamlit...")
    print("📊 El dashboard se abrirá en http://localhost:8501")
    
    # Iniciar streamlit en background
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(dashboard_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Esperar un poco para que Streamlit inicie
    time.sleep(3)
    
    print("✅ Dashboard iniciado!")
    return process


def run_system_with_enhanced_recorder(args):
    """Ejecuta el sistema con EnhancedRecorder."""
    from datetime import datetime
    from coreee.llm_client import CloudflareLLMClient
    from coreee.sistema_agentes_supervisor_coder import MiniAgentSystem
    from coreee.session_manager import SessionManager
    from coreee.agent_registry import AgentRegistry
    from coreee.enhanced_recorder import EnhancedRecorder
    
    # Crear session_id
    session_id = args.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Crear directorio de logs
    session_dir = Path(args.log_dir) / datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    # Crear EnhancedRecorder (usa EventBus automáticamente)
    recorder = EnhancedRecorder(str(session_dir), session_id=session_id)
    
    # Emitir evento de inicio de sesión
    recorder.emit_session_start(turn=0, task=args.task)
    
    print(f"\n{'='*60}")
    print(f"🤖 AutoAgent con Visualización en Tiempo Real")
    print(f"{'='*60}")
    print(f"📊 Dashboard: http://localhost:8501")
    print(f"🎯 Sesión: {session_id}")
    print(f"📁 Logs: {session_dir}")
    print(f"{'='*60}\n")
    
    # Crear sistema
    llm = CloudflareLLMClient()
    session_mgr = SessionManager(args.sessions_dir)
    agent_registry = AgentRegistry(llm, args.agents_dir, session_id=session_id)
    
    system = MiniAgentSystem(
        llm,
        recorder=recorder,
        session_manager=session_mgr,
        agent_registry=agent_registry
    )
    
    try:
        # Ejecutar tarea
        result = system.run(
            task=args.task,
            max_turns=args.max_turns,
            stream=True,
            session_id=session_id,
            resume_session=args.resume_session
        )
        
        # Emitir evento de fin
        status = "completed" if result.get("success") else "failed"
        recorder.emit_session_end(
            turn=result.get("turn", 0),
            status=status,
            summary=result.get("final_answer", "")
        )
        
        print(f"\n{'='*60}")
        print(f"✅ Sesión completada: {status}")
        print(f"📊 Revisa el dashboard para ver todos los detalles")
        print(f"{'='*60}\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Ejecución interrumpida por el usuario")
        recorder.emit_session_end(turn=0, status="interrupted", summary="Usuario interrumpió la ejecución")
    except Exception as e:
        print(f"\n\n❌ Error durante la ejecución: {e}")
        import traceback
        recorder.emit_error(
            turn=0,
            error_type="execution_error",
            message=str(e),
            traceback=traceback.format_exc()
        )
        raise


def main():
    parser = argparse.ArgumentParser(description='AutoAgent con Dashboard en Tiempo Real')
    
    # Argumentos del sistema
    parser.add_argument('-q', '--task', required=True, help='Tarea a resolver')
    parser.add_argument('-m', '--max-turns', dest='max_turns', type=int, default=10, help='Máximo de turnos')
    parser.add_argument('--log-dir', dest='log_dir', default='.runs', help='Directorio de logs')
    parser.add_argument('--session-id', dest='session_id', help='ID de sesión')
    parser.add_argument('--resume', dest='resume_session', action='store_true', help='Reanudar sesión')
    parser.add_argument('--sessions-dir', dest='sessions_dir', default='.sessions', help='Directorio de sesiones')
    parser.add_argument('--agents-dir', dest='agents_dir', default='.agents', help='Directorio de agentes')
    
    # Opciones del dashboard
    parser.add_argument('--no-dashboard', action='store_true', help='No iniciar dashboard automáticamente')
    parser.add_argument('--dashboard-only', action='store_true', help='Solo iniciar dashboard (sin ejecutar sistema)')
    
    args = parser.parse_args()
    
    # Si solo queremos el dashboard
    if args.dashboard_only:
        print("📊 Iniciando solo el dashboard...")
        dashboard_process = start_dashboard()
        print("\n✅ Dashboard ejecutándose en http://localhost:8501")
        print("⌨️  Presiona Ctrl+C para detener")
        try:
            dashboard_process.wait()
        except KeyboardInterrupt:
            print("\n\n👋 Dashboard detenido")
            dashboard_process.terminate()
        return
    
    # Iniciar dashboard si no se especifica lo contrario
    dashboard_process = None
    if not args.no_dashboard:
        try:
            dashboard_process = start_dashboard()
        except Exception as e:
            print(f"⚠️ No se pudo iniciar el dashboard: {e}")
            print("💡 Puedes iniciarlo manualmente: streamlit run dashboard_streamlit.py")
            print("Continuando sin dashboard...\n")
    
    try:
        # Ejecutar sistema
        run_system_with_enhanced_recorder(args)
    finally:
        # Cerrar dashboard si lo iniciamos
        if dashboard_process:
            print("\n🛑 Cerrando dashboard...")
            dashboard_process.terminate()
            time.sleep(1)
            if dashboard_process.poll() is None:
                dashboard_process.kill()


if __name__ == "__main__":
    main()
