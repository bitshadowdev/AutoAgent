#!/usr/bin/env python
"""
Utilidad CLI para gestionar sesiones persistentes.

Comandos disponibles:
    python manage_sessions.py list [--status STATUS] [--limit N]
    python manage_sessions.py show SESSION_ID
    python manage_sessions.py delete SESSION_ID
    python manage_sessions.py export SESSION_ID [--output FILE]
    python manage_sessions.py import FILE
    python manage_sessions.py clean [--status STATUS] [--days N]
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

try:
    from session_manager import SessionManager
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from session_manager import SessionManager


def list_sessions(manager: SessionManager, status: Optional[str] = None, limit: Optional[int] = None):
    """Lista sesiones con formato tabular"""
    sessions = manager.list_sessions(status=status, limit=limit)
    
    if not sessions:
        print("No hay sesiones guardadas.")
        return
    
    print(f"\n{'ID':<30} {'Tarea':<50} {'Estado':<12} {'Última modificación':<25} {'Turnos':<8}")
    print("=" * 135)
    
    for s in sessions:
        session_id = s['session_id'][:30]
        task = s.get('task', 'N/A')[:50]
        status_val = s.get('status', 'unknown')
        updated = s.get('updated_at', 'N/A')[:25]
        
        # Cargar sesión para obtener turnos
        session_data = manager.load_session(s['session_id'])
        turns = str(session_data.metadata.total_turns) if session_data else 'N/A'
        
        # Icono de estado
        if status_val == 'completed':
            icon = '✓'
        elif status_val == 'active':
            icon = '○'
        else:
            icon = '✗'
        
        print(f"{icon} {session_id:<28} {task:<50} {status_val:<12} {updated:<25} {turns:<8}")
    
    print(f"\nTotal: {len(sessions)} sesiones")


def show_session(manager: SessionManager, session_id: str):
    """Muestra detalles completos de una sesión"""
    session = manager.load_session(session_id)
    
    if not session:
        print(f"No se encontró la sesión '{session_id}'")
        return
    
    print(f"\n{'='*60}")
    print(f"SESIÓN: {session_id}")
    print(f"{'='*60}\n")
    
    meta = session.metadata
    print(f"Tarea:              {meta.task}")
    print(f"Estado:             {meta.status}")
    print(f"Modelo:             {meta.model}")
    print(f"Creada:             {meta.created_at}")
    print(f"Actualizada:        {meta.updated_at}")
    print(f"Total de turnos:    {meta.total_turns}")
    print(f"Tags:               {', '.join(meta.tags) if meta.tags else 'ninguno'}")
    
    if session.tools_used:
        print(f"\nHerramientas usadas ({len(session.tools_used)}):")
        for tool in session.tools_used:
            print(f"  - {tool}")
    
    print(f"\nTranscript ({len(session.transcript)} mensajes):")
    for i, msg in enumerate(session.transcript, 1):
        role = msg.get('role', 'unknown').upper()
        content = msg.get('content', '')[:100]
        print(f"  {i}. [{role}] {content}...")
    
    if session.custom_data:
        print(f"\nDatos personalizados:")
        print(json.dumps(session.custom_data, indent=2, ensure_ascii=False))


def delete_session(manager: SessionManager, session_id: str):
    """Elimina una sesión"""
    if not manager.session_exists(session_id):
        print(f"No se encontró la sesión '{session_id}'")
        return
    
    response = input(f"¿Eliminar sesión '{session_id}'? (s/n): ")
    if response.lower() == 's':
        if manager.delete_session(session_id):
            print(f"Sesión '{session_id}' eliminada correctamente.")
        else:
            print(f"Error al eliminar la sesión.")
    else:
        print("Operación cancelada.")


def export_session(manager: SessionManager, session_id: str, output: Optional[str] = None):
    """Exporta una sesión a JSON"""
    session = manager.load_session(session_id)
    
    if not session:
        print(f"No se encontró la sesión '{session_id}'")
        return
    
    output_path = output or f"{session_id}_export.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
    
    print(f"Sesión exportada a: {output_path}")


def import_session(manager: SessionManager, file_path: str):
    """Importa una sesión desde JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        from session_manager import SessionData
        session = SessionData.from_dict(data)
        
        # Guardar sesión importada
        manager.save_session(
            session_id=session.metadata.session_id,
            transcript=session.transcript,
            metadata=session.metadata.to_dict(),
            tools_used=session.tools_used,
            custom_data=session.custom_data,
            status=session.metadata.status
        )
        
        print(f"Sesión '{session.metadata.session_id}' importada correctamente.")
    except Exception as e:
        print(f"Error al importar sesión: {e}")


def clean_sessions(manager: SessionManager, status: Optional[str] = None, days: Optional[int] = None):
    """Limpia sesiones antiguas o con cierto estado"""
    sessions = manager.list_sessions()
    
    if not sessions:
        print("No hay sesiones para limpiar.")
        return
    
    to_delete = []
    now = datetime.utcnow()
    
    for s in sessions:
        should_delete = False
        
        # Filtrar por estado
        if status and s.get('status') == status:
            should_delete = True
        
        # Filtrar por antigüedad
        if days:
            try:
                updated_at = datetime.fromisoformat(s.get('updated_at', '').replace('Z', '+00:00'))
                if (now - updated_at.replace(tzinfo=None)) > timedelta(days=days):
                    should_delete = True
            except Exception:
                pass
        
        if should_delete:
            to_delete.append(s['session_id'])
    
    if not to_delete:
        print("No se encontraron sesiones que cumplan los criterios.")
        return
    
    print(f"\nSesiones a eliminar ({len(to_delete)}):")
    for sid in to_delete:
        print(f"  - {sid}")
    
    response = input(f"\n¿Eliminar {len(to_delete)} sesiones? (s/n): ")
    if response.lower() == 's':
        for sid in to_delete:
            manager.delete_session(sid)
        print(f"{len(to_delete)} sesiones eliminadas.")
    else:
        print("Operación cancelada.")


def main():
    parser = argparse.ArgumentParser(
        description='Gestor de sesiones persistentes para AutoAgent',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--sessions-dir', default='.sessions', help='Directorio de sesiones')
    
    subparsers = parser.add_subparsers(dest='command', help='Comando a ejecutar')
    
    # list
    list_parser = subparsers.add_parser('list', help='Listar sesiones')
    list_parser.add_argument('--status', choices=['active', 'completed', 'error'], help='Filtrar por estado')
    list_parser.add_argument('--limit', type=int, help='Limitar número de resultados')
    
    # show
    show_parser = subparsers.add_parser('show', help='Mostrar detalles de una sesión')
    show_parser.add_argument('session_id', help='ID de la sesión')
    
    # delete
    delete_parser = subparsers.add_parser('delete', help='Eliminar una sesión')
    delete_parser.add_argument('session_id', help='ID de la sesión')
    
    # export
    export_parser = subparsers.add_parser('export', help='Exportar una sesión a JSON')
    export_parser.add_argument('session_id', help='ID de la sesión')
    export_parser.add_argument('--output', help='Archivo de salida')
    
    # import
    import_parser = subparsers.add_parser('import', help='Importar una sesión desde JSON')
    import_parser.add_argument('file', help='Archivo JSON a importar')
    
    # clean
    clean_parser = subparsers.add_parser('clean', help='Limpiar sesiones antiguas')
    clean_parser.add_argument('--status', choices=['active', 'completed', 'error'], help='Estado a eliminar')
    clean_parser.add_argument('--days', type=int, help='Eliminar sesiones más antiguas que N días')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = SessionManager(args.sessions_dir)
    
    if args.command == 'list':
        list_sessions(manager, status=args.status, limit=args.limit)
    elif args.command == 'show':
        show_session(manager, args.session_id)
    elif args.command == 'delete':
        delete_session(manager, args.session_id)
    elif args.command == 'export':
        export_session(manager, args.session_id, args.output)
    elif args.command == 'import':
        import_session(manager, args.file)
    elif args.command == 'clean':
        clean_sessions(manager, status=args.status, days=args.days)


if __name__ == '__main__':
    main()
