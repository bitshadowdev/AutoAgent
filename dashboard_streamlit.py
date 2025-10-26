"""
Dashboard en tiempo real para visualizar la ejecución del sistema AutoAgent.

Usa Streamlit para mostrar:
- Timeline de eventos
- Mensajes entre agentes y usuarios
- Herramientas creadas con su código
- Invocaciones de herramientas
- Estadísticas en tiempo real

Ejecutar:
    streamlit run dashboard_streamlit.py
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import List, Dict, Any
import time

# Agregar coreee al path
sys.path.insert(0, str(Path(__file__).parent))

from coreee.event_bus import get_event_bus, SystemEvent, EventLogger

# Configuración de la página
st.set_page_config(
    page_title="AutoAgent Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .event-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid;
    }
    .event-user { border-left-color: #3b82f6; background-color: #dbeafe; }
    .event-coder { border-left-color: #10b981; background-color: #d1fae5; }
    .event-supervisor { border-left-color: #f59e0b; background-color: #fef3c7; }
    .event-agent { border-left-color: #8b5cf6; background-color: #ede9fe; }
    .event-tool { border-left-color: #ec4899; background-color: #fce7f3; }
    .event-system { border-left-color: #6b7280; background-color: #f3f4f6; }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
    }
    
    .code-block {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.9rem;
        overflow-x: auto;
    }
    
    .timeline-item {
        border-left: 2px solid #e5e7eb;
        padding-left: 1.5rem;
        margin-bottom: 1.5rem;
        position: relative;
    }
    
    .timeline-dot {
        position: absolute;
        left: -0.5rem;
        width: 1rem;
        height: 1rem;
        border-radius: 50%;
        background-color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)


def format_timestamp(ts: str) -> str:
    """Formatea timestamp ISO a formato legible."""
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime("%H:%M:%S")
    except:
        return ts


def get_role_emoji(role: str) -> str:
    """Devuelve emoji según el rol."""
    emojis = {
        "user": "👤",
        "coder": "💻",
        "supervisor": "👔",
        "agent": "🤖",
        "tool": "🔧",
        "system": "⚙️"
    }
    return emojis.get(role.lower(), "📌")


def get_role_color(role: str) -> str:
    """Devuelve color según el rol."""
    colors = {
        "user": "#3b82f6",
        "coder": "#10b981",
        "supervisor": "#f59e0b",
        "agent": "#8b5cf6",
        "tool": "#ec4899",
        "system": "#6b7280"
    }
    return colors.get(role.lower(), "#6b7280")


def render_event_card(event: SystemEvent, show_data: bool = False):
    """Renderiza una tarjeta de evento."""
    role_emoji = get_role_emoji(event.role)
    time_str = format_timestamp(event.ts)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 6, 2])
        
        with col1:
            st.markdown(f"### {role_emoji}")
        
        with col2:
            st.markdown(f"**{event.role.upper()}** · {event.etype}")
            if event.summary:
                st.markdown(event.summary)
            
            # Mostrar información específica según el tipo
            if event.tool_name:
                st.caption(f"🔧 Tool: `{event.tool_name}`")
            if event.agent_name:
                st.caption(f"🤖 Agent: `{event.agent_name}`")
            
            # Datos adicionales
            if show_data and event.data:
                with st.expander("📊 Datos del evento"):
                    st.json(event.data)
        
        with col3:
            st.caption(f"⏱️ {time_str}")
            st.caption(f"Turn {event.turn}")
        
        st.divider()


def render_tool_code(tool_name: str, code: str):
    """Renderiza código de herramienta con syntax highlighting."""
    st.markdown(f"### 🔧 {tool_name}")
    st.code(code, language="python", line_numbers=True)


def render_message(event: SystemEvent):
    """Renderiza un mensaje de chat."""
    role_emoji = get_role_emoji(event.role)
    
    # Construir contenido según el tipo de evento
    if event.etype == "coder_final_proposal":
        content = f"<strong>Respuesta Final:</strong><br/>{event.data.get('answer', event.summary)}"
    elif event.etype == "supervisor_decision":
        route = event.data.get('route', 'unknown')
        reason = event.data.get('reason', '')
        tips = event.data.get('tips', [])
        
        if route == 'end':
            content = f"<strong>✅ Decisión: Finalizar</strong><br/>{reason}"
        else:
            content = f"<strong>🔄 Decisión: Continuar</strong><br/>{reason}"
            if tips:
                tips_html = "<br/>".join(f"• {tip}" for tip in tips[:3])  # Mostrar primeros 3 tips
                content += f"<br/><br/><small><strong>Sugerencias:</strong><br/>{tips_html}</small>"
    elif event.etype == "tool_result_ok":
        tool_name = event.data.get('tool_name', 'herramienta')
        result = event.data.get('result', {})
        content = f"<strong>✅ {tool_name}</strong><br/>Resultado: {result}"
    elif event.etype == "tool_result_error":
        tool_name = event.data.get('tool_name', 'herramienta')
        error = event.data.get('error', 'Error desconocido')
        content = f"<strong>❌ {tool_name}</strong><br/>Error: {error}"
    elif event.etype == "agent_response_ok":
        agent_name = event.data.get('agent_name', 'agente')
        response = event.data.get('response', event.summary)
        content = f"<strong>🤖 {agent_name}</strong><br/>{response}"
    else:
        content = event.data.get("content", event.summary)
    
    # Determinar alineación según el rol
    is_user = event.role.lower() == "user"
    
    if is_user:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div style="background-color: #dbeafe; padding: 1rem; border-radius: 1rem; margin-bottom: 0.5rem;">
                <strong>{role_emoji} Usuario</strong><br/>
                {content}
            </div>
            """, unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([1, 3])
        with col2:
            color = get_role_color(event.role)
            st.markdown(f"""
            <div style="background-color: {color}20; padding: 1rem; border-radius: 1rem; margin-bottom: 0.5rem; border-left: 4px solid {color};">
                <strong>{role_emoji} {event.role.title()}</strong><br/>
                {content}
            </div>
            """, unsafe_allow_html=True)


def main():
    """Función principal del dashboard."""
    
    # Inicializar session_state temprano
    if 'auto_load_path' not in st.session_state:
        st.session_state.auto_load_path = None
    if 'events' not in st.session_state:
        st.session_state.events = []
    if 'last_event_count' not in st.session_state:
        st.session_state.last_event_count = 0
    if 'manual_mode' not in st.session_state:
        st.session_state.manual_mode = False  # False = auto-detect, True = archivo fijo
    
    # Header
    st.title("🤖 AutoAgent Real-Time Dashboard")
    
    # Mostrar origen de datos y modo
    if st.session_state.auto_load_path:
        mode_badge = "📌 FIJO" if st.session_state.manual_mode else "🔄 AUTO-DETECT"
        st.info(f"{mode_badge} | Cargando eventos desde: `{st.session_state.auto_load_path}`")
    else:
        st.info("💾 Esperando eventos... (Modo auto-detección)")
    
    st.markdown("---")
    
    # Sidebar - Configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Opciones de visualización
        show_data = st.checkbox("Mostrar datos de eventos", value=False)
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        refresh_interval = st.slider("Intervalo (segundos)", 1, 10, 2)
        
        # Filtros
        st.header("🔍 Filtros")
        filter_roles = st.multiselect(
            "Roles",
            ["user", "coder", "supervisor", "agent", "tool", "system"],
            default=["user", "coder", "supervisor", "agent", "tool", "system"]
        )
        
        filter_etypes = st.text_input("Tipo de evento (regex)", "")
        
        # Opciones de archivo
        st.header("📁 Gestión de Archivos")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Auto-detectar"):
                st.session_state.auto_load_path = None
                st.session_state.manual_mode = False
                st.success("Modo auto-detección activado")
        
        with col2:
            if st.button("📊 Refrescar"):
                st.rerun()
        
        st.markdown("---")
        
        log_file = st.text_input("Ruta manual:", ".runs/2025-10-26_13-20-00/events.jsonl")
        if st.button("📂 Cargar archivo específico"):
            if Path(log_file).exists():
                st.session_state.load_from_file = log_file
                st.success(f"Cargando eventos de {log_file}")
            else:
                st.error("Archivo no encontrado")
        
        # Mostrar archivo actual
        if st.session_state.auto_load_path:
            st.caption(f"📄 Archivo actual:")
            st.code(st.session_state.auto_load_path, language="text")
    
    # Obtener EventBus
    event_bus = get_event_bus()
    
    # Cargar eventos del archivo si se solicitó manualmente
    if 'load_from_file' in st.session_state:
        log_path = st.session_state.load_from_file
        try:
            events = EventLogger.read_events(log_path)
            st.session_state.events = events
            st.session_state.last_event_count = len(events)
            st.session_state.auto_load_path = log_path
            st.session_state.manual_mode = True  # Activar modo manual
            del st.session_state.load_from_file
        except Exception as e:
            st.error(f"Error cargando eventos: {e}")
    elif st.session_state.manual_mode and st.session_state.auto_load_path:
        # Modo manual: leer solo del archivo fijado
        try:
            events = EventLogger.read_events(st.session_state.auto_load_path)
            st.session_state.events = events
            st.session_state.last_event_count = len(events)
        except Exception as e:
            st.error(f"Error leyendo archivo: {e}")
    else:
        # Modo auto-detección: SIEMPRE buscar el archivo MÁS reciente
        runs_dir = Path(".runs")
        latest_found = None
        
        if runs_dir.exists():
            # Buscar el directorio más reciente por timestamp
            run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
            if run_dirs:
                latest_events = run_dirs[0] / "events.jsonl"
                if latest_events.exists():
                    latest_found = str(latest_events)
        
        # Si encontramos un archivo más nuevo, cambiar a él
        if latest_found:
            # Verificar si es diferente al actual (notificar cambio)
            if st.session_state.auto_load_path != latest_found:
                st.session_state.auto_load_path = latest_found
                st.success(f"🆕 Detectada nueva sesión: `{latest_found}`")
            
            # Cargar eventos (siempre, para actualizaciones)
            try:
                events = EventLogger.read_events(latest_found)
                st.session_state.events = events
                st.session_state.last_event_count = len(events)
            except Exception:
                # Si falla, usar bus en memoria
                events = event_bus.get_history()
                st.session_state.events = events
                st.session_state.last_event_count = len(events)
        else:
            # No hay archivos, usar bus en memoria
            events = event_bus.get_history()
            st.session_state.events = events
            st.session_state.last_event_count = len(events)
    
    # Aplicar filtros
    filtered_events = [
        e for e in st.session_state.events
        if e.role.lower() in [r.lower() for r in filter_roles]
    ]
    
    if filter_etypes:
        import re
        try:
            pattern = re.compile(filter_etypes, re.IGNORECASE)
            filtered_events = [e for e in filtered_events if pattern.search(e.etype)]
        except:
            st.sidebar.error("Regex inválido")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Eventos", len(filtered_events))
    
    with col2:
        stats = event_bus.get_stats()
        st.metric("👂 Listeners", stats["total_listeners"])
    
    with col3:
        unique_sessions = len(set(e.session_id for e in filtered_events if e.session_id))
        st.metric("🎯 Sesiones", unique_sessions)
    
    with col4:
        if filtered_events:
            last_event = filtered_events[-1]
            st.metric("⏱️ Último", format_timestamp(last_event.ts))
    
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Timeline",
        "💬 Mensajes",
        "🔧 Herramientas",
        "📊 Estadísticas",
        "🔍 Inspector"
    ])
    
    # TAB 1: Timeline completo
    with tab1:
        st.header("📋 Timeline de Eventos")
        
        if not filtered_events:
            st.info("No hay eventos para mostrar. El sistema está esperando eventos...")
        else:
            # Mostrar eventos en orden cronológico inverso (más recientes primero)
            for event in reversed(filtered_events[-50:]):  # Últimos 50 eventos
                render_event_card(event, show_data=show_data)
    
    # TAB 2: Vista de mensajes (chat-like)
    with tab2:
        st.header("💬 Conversación")
        
        # Incluir eventos conversacionales: mensajes explícitos, propuestas, resultados
        message_events = [
            e for e in filtered_events
            if (
                "message" in e.etype.lower() or
                e.role in ["user", "coder", "supervisor", "agent"] or
                e.etype in ["coder_final_proposal", "tool_result_ok", "tool_result_error", "agent_response_ok", "agent_response_error"]
            )
        ]
        
        if not message_events:
            st.info("No hay mensajes para mostrar")
        else:
            for event in message_events[-50:]:  # Últimos 50 mensajes
                render_message(event)
    
    # TAB 3: Herramientas creadas
    with tab3:
        st.header("🔧 Herramientas Creadas/Actualizadas")
        
        tool_events = [
            e for e in filtered_events
            if e.etype in ["tool_create", "tool_update"] or 
               ("tool" in e.etype.lower() and ("create" in e.etype.lower() or "update" in e.etype.lower()))
        ]
        
        # Debug: mostrar info de eventos de herramientas encontrados
        if show_data and tool_events:
            st.caption(f"🔍 Debug: Encontrados {len(tool_events)} eventos de herramientas")
            for evt in tool_events[:3]:  # Mostrar primeros 3
                st.caption(f"  • {evt.etype} - tool_name: {evt.data.get('tool_name', 'N/A')}")
        
        if not tool_events:
            st.info("No se han creado herramientas aún")
        else:
            # Agrupar por nombre de herramienta
            tools_by_name = {}
            for event in tool_events:
                tool_name = event.data.get("tool_name", "")
                if not tool_name and hasattr(event, 'tool_name'):
                    tool_name = event.tool_name
                if tool_name:
                    if tool_name not in tools_by_name:
                        tools_by_name[tool_name] = []
                    tools_by_name[tool_name].append(event)
            
            # Mostrar cada herramienta
            for tool_name, events in tools_by_name.items():
                with st.expander(f"🔧 {tool_name} ({len(events)} versión/es)", expanded=True):
                    for i, event in enumerate(reversed(events), 1):
                        st.markdown(f"**Versión {len(events) - i + 1}** - {format_timestamp(event.ts)}")
                        
                        # Intentar obtener código de data.code primero
                        code = event.data.get("code", "")
                        
                        # Si no hay código, intentar leer del archivo code_path
                        if not code and event.data.get("code_path"):
                            code_path = Path(event.data.get("code_path"))
                            if code_path.exists():
                                try:
                                    code = code_path.read_text(encoding='utf-8')
                                except:
                                    pass
                        
                        if code:
                            st.code(code, language="python", line_numbers=True)
                        else:
                            st.warning("Código no disponible")
                        
                        # Mostrar información adicional
                        if event.data.get("chars"):
                            st.caption(f"📊 {event.data.get('chars')} caracteres")
                        
                        st.divider()
    
    # TAB 4: Estadísticas
    with tab4:
        st.header("📊 Estadísticas")
        
        stats = event_bus.get_stats()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Por Tipo de Evento")
            if stats["events_by_type"]:
                import pandas as pd
                df_types = pd.DataFrame(
                    list(stats["events_by_type"].items()),
                    columns=["Tipo", "Cantidad"]
                ).sort_values("Cantidad", ascending=False)
                st.bar_chart(df_types.set_index("Tipo"))
            else:
                st.info("No hay datos")
        
        with col2:
            st.subheader("Por Rol")
            if stats["events_by_role"]:
                import pandas as pd
                df_roles = pd.DataFrame(
                    list(stats["events_by_role"].items()),
                    columns=["Rol", "Cantidad"]
                ).sort_values("Cantidad", ascending=False)
                st.bar_chart(df_roles.set_index("Rol"))
            else:
                st.info("No hay datos")
        
        # Timeline de actividad
        st.subheader("📈 Actividad en el Tiempo")
        if filtered_events:
            import pandas as pd
            # Crear DataFrame con timestamps
            df = pd.DataFrame([{
                "timestamp": datetime.fromisoformat(e.ts.replace('Z', '+00:00')),
                "rol": e.role
            } for e in filtered_events])
            
            # Agrupar por minuto
            df['minute'] = df['timestamp'].dt.floor('1min')
            activity = df.groupby('minute').size().reset_index(name='eventos')
            
            st.line_chart(activity.set_index('minute'))
        else:
            st.info("No hay datos para mostrar")
    
    # TAB 5: Inspector de eventos
    with tab5:
        st.header("🔍 Inspector de Eventos")
        
        if filtered_events:
            # Selector de evento
            event_idx = st.selectbox(
                "Seleccionar evento",
                range(len(filtered_events)),
                format_func=lambda i: f"{i+1}. {filtered_events[i].etype} - {format_timestamp(filtered_events[i].ts)}"
            )
            
            selected_event = filtered_events[event_idx]
            
            # Mostrar detalles completos
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📋 Metadata")
                st.json({
                    "timestamp": selected_event.ts,
                    "turn": selected_event.turn,
                    "role": selected_event.role,
                    "etype": selected_event.etype,
                    "session_id": selected_event.session_id,
                    "agent_name": selected_event.agent_name,
                    "tool_name": selected_event.tool_name
                })
            
            with col2:
                st.subheader("📊 Datos")
                st.json(selected_event.data)
            
            st.subheader("📝 Summary")
            st.text(selected_event.summary)
            
            st.subheader("💾 JSON Completo")
            st.json(selected_event.to_dict())
        else:
            st.info("No hay eventos para inspeccionar")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
