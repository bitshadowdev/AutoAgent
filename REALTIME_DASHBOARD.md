# 📊 Dashboard en Tiempo Real - AutoAgent

Sistema completo de visualización en tiempo real de todos los eventos del sistema AutoAgent usando Streamlit.

**Fecha**: 26 Octubre 2025  
**Estado**: ✅ **IMPLEMENTADO**

---

## 🎯 Características

### Eventos Capturados

El dashboard captura y visualiza **TODO** lo que sucede en el sistema:

✅ **Mensajes entre agentes y usuarios**
- Conversación completa estilo chat
- Distingue entre usuario, Coder, Supervisor, agentes dinámicos

✅ **Herramientas creadas/actualizadas**
- Código completo con syntax highlighting
- Historial de versiones de cada herramienta
- Momento exacto de creación/modificación

✅ **Invocaciones de herramientas**
- Argumentos pasados a cada herramienta
- Resultados (éxito o error)
- Tiempo de ejecución

✅ **Acciones de agentes dinámicos**
- Creación de nuevos agentes
- Invocaciones de agentes
- Respuestas de agentes

✅ **Eventos del sistema**
- Inicio/fin de sesión
- Cambios de turno
- Errores y excepciones

✅ **Timeline completo**
- Cronología exacta de todos los eventos
- Filtros por rol, tipo de evento
- Búsqueda y navegación

✅ **Estadísticas en tiempo real**
- Eventos por tipo
- Eventos por rol
- Actividad en el tiempo
- Métricas de performance

---

## 🚀 Instalación

### 1. Instalar Streamlit

```bash
pip install streamlit pandas
```

### 2. Verificar instalación

```bash
streamlit --version
```

---

## 💻 Uso

### Opción 1: Ejecución Automática (Recomendado)

El script `run_with_dashboard.py` inicia el dashboard y el sistema automáticamente:

```bash
python run_with_dashboard.py -q "tu tarea aquí"
```

Esto:
1. ✅ Inicia el dashboard en http://localhost:8501
2. ✅ Ejecuta el sistema con EnhancedRecorder
3. ✅ Visualiza eventos en tiempo real
4. ✅ Cierra todo al terminar

### Opción 2: Dashboard Solo (sin ejecutar tarea)

Útil para visualizar sesiones antiguas:

```bash
python run_with_dashboard.py --dashboard-only
```

Luego, en el dashboard:
- Usa el sidebar → "Cargar desde archivo"
- Especifica la ruta a `events.jsonl` (ej: `.runs/2025-10-26_10-30-15/events.jsonl`)

### Opción 3: Ejecución Manual (Dos Terminales)

**Terminal 1 - Dashboard:**
```bash
streamlit run dashboard_streamlit.py
```

**Terminal 2 - Sistema:**
```bash
python coreee/sistema_agentes_supervisor_coder.py -q "tu tarea"
```

---

## 🎨 Interfaz del Dashboard

### Tab 1: 📋 Timeline

Vista cronológica completa de todos los eventos:

```
┌─────────────────────────────────────────┐
│ 💻 CODER · tool_created                 │
│ Creada herramienta: fetch_news          │
│ 🔧 Tool: fetch_news                     │
│ ⏱️ 14:30:25    Turn 3                   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 🔧 TOOL · tool_called                   │
│ Llamada a herramienta: fetch_news       │
│ 🔧 Tool: fetch_news                     │
│ ⏱️ 14:30:28    Turn 3                   │
└─────────────────────────────────────────┘
```

**Características:**
- Últimos 50 eventos
- Ordenados del más reciente al más antiguo
- Código de colores por rol
- Expandible para ver datos JSON

### Tab 2: 💬 Mensajes

Vista estilo chat de la conversación:

```
┌─────────────────────────────────┐
│ 👤 Usuario                      │
│ Busca noticias de IA            │
└─────────────────────────────────┘

        ┌─────────────────────────────────┐
        │ 💻 Coder                        │
        │ Voy a crear una herramienta     │
        │ para buscar noticias...         │
        └─────────────────────────────────┘

┌─────────────────────────────────┐
│ 👤 Usuario                      │
│ Perfecto, muéstrame los         │
│ resultados                      │
└─────────────────────────────────┘
```

**Características:**
- Interfaz tipo chat
- Mensajes de usuario a la izquierda
- Mensajes del sistema a la derecha
- Últimos 30 mensajes

### Tab 3: 🔧 Herramientas

Código completo de todas las herramientas creadas:

```python
🔧 fetch_news (2 versión/es)

Versión 2 - 14:32:15
───────────────────────────────────
def fetch_news(args):
    import requests
    api_key = args.get('api_key')
    query = args.get('query', 'AI')
    
    # Código actualizado con manejo de errores
    try:
        response = requests.get(...)
        return {"ok": True, "news": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}
```

**Características:**
- Historial completo de versiones
- Syntax highlighting para Python
- Números de línea
- Timestamps de cada versión

### Tab 4: 📊 Estadísticas

Visualizaciones y métricas:

```
┌─────────────────────────────────────────┐
│ Por Tipo de Evento                      │
│                                         │
│ tool_created     ████████████  12       │
│ tool_called      ██████████    10       │
│ message_user     ████████       8       │
│ agent_response   ██████         6       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Por Rol                                 │
│                                         │
│ coder      ████████████████  20         │
│ tool       ████████████      15         │
│ user       ██████             8         │
│ agent      ████               5         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 📈 Actividad en el Tiempo               │
│                                         │
│     ╱╲                                  │
│    ╱  ╲      ╱╲                         │
│   ╱    ╲    ╱  ╲                        │
│  ╱      ╲  ╱    ╲                       │
│ ╱        ╲╱      ╲                      │
└─────────────────────────────────────────┘
```

**Características:**
- Gráficos de barras interactivos
- Timeline de actividad
- Distribuciones por tipo y rol

### Tab 5: 🔍 Inspector

Inspector detallado de eventos individuales:

```json
{
  "timestamp": "2025-10-26T14:30:25Z",
  "turn": 3,
  "role": "coder",
  "etype": "tool_created",
  "session_id": "20251026_143000",
  "tool_name": "fetch_news",
  "data": {
    "tool_name": "fetch_news",
    "code": "def fetch_news(args): ...",
    "code_length": 450,
    "is_update": false
  }
}
```

**Características:**
- Vista JSON completa
- Metadata y datos separados
- Navegación evento por evento

---

## ⚙️ Sidebar - Configuración y Filtros

### Opciones de Visualización

```
☑️ Mostrar datos de eventos
☑️ Auto-refresh
Intervalo: ⚫━━━━━━━ 2 segundos
```

### Filtros

```
🔍 Filtros
─────────────────────────────
Roles:
☑️ user
☑️ coder
☑️ supervisor
☑️ agent
☑️ tool
☑️ system

Tipo de evento (regex):
[tool_.*]

Total filtrados: 25 eventos
```

### Cargar desde Archivo

```
📁 Cargar desde archivo
─────────────────────────────
Ruta: .runs/*/events.jsonl
        [📂 Cargar archivo]
```

---

## 🔧 Arquitectura Técnica

### Componentes

```
┌────────────────────────────────────────────────────┐
│              MiniAgentSystem                       │
│                                                    │
│  ┌──────────────┐      ┌───────────────┐          │
│  │  Supervisor  │◄────►│    Coder      │          │
│  └──────────────┘      └───────┬───────┘          │
│                                 │                  │
│                                 ▼                  │
│                        ┌────────────────┐          │
│                        │ Enhanced       │          │
│                        │ Recorder       │          │
│                        └────────┬───────┘          │
└─────────────────────────────────┼──────────────────┘
                                  │
                                  ▼
                        ┌────────────────┐
                        │   EventBus     │
                        │   (Global)     │
                        └────────┬───────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
          ┌─────────────────┐         ┌─────────────────┐
          │   EventLogger   │         │   Streamlit     │
          │   (to JSONL)    │         │   Dashboard     │
          └─────────────────┘         └─────────────────┘
                  │                           │
                  ▼                           ▼
          events.jsonl                 Browser UI
```

### Flujo de Eventos

1. **Sistema emite evento** → `recorder.emit(...)`
2. **EnhancedRecorder** →
   - Guarda a JSONL (como siempre)
   - Emite a EventBus
3. **EventBus** →
   - Notifica a listeners (Streamlit)
   - Mantiene historial en memoria
4. **Dashboard Streamlit** →
   - Recibe evento via EventBus
   - Actualiza UI en tiempo real
   - Auto-refresh cada N segundos

### EventBus (Thread-Safe)

```python
from coreee.event_bus import get_event_bus

# Obtener instancia global
bus = get_event_bus()

# Suscribir listener
def my_listener(event):
    print(f"Evento: {event.etype}")

bus.subscribe(my_listener)

# Emitir evento
bus.emit(
    turn=1,
    role="coder",
    etype="tool_created",
    summary="Nueva herramienta",
    data={"tool_name": "mi_tool"}
)
```

### EnhancedRecorder (Compatible)

```python
from coreee.enhanced_recorder import EnhancedRecorder

# Crear recorder (compatible 100% con Recorder original)
recorder = EnhancedRecorder(root=".runs/session", session_id="123")

# API original funciona igual
recorder.emit(turn=1, role="coder", etype="test", summary="Hola")

# API extendida para casos comunes
recorder.emit_tool_creation(turn=1, tool_name="test", code="...", is_update=False)
recorder.emit_user_message(turn=1, content="Hola sistema")
recorder.emit_agent_action(turn=1, agent_name="analyst", action="analyze", details={})
```

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Ejecutar con Dashboard

```bash
python run_with_dashboard.py -q "Busca las últimas noticias de IA y resúmelas"
```

**Lo que verás:**
1. Dashboard se abre en el navegador
2. Sistema comienza a ejecutar la tarea
3. Eventos aparecen en tiempo real:
   - Mensaje del usuario
   - Coder crea herramienta `fetch_news`
   - Herramienta se invoca
   - Resultados aparecen
   - Coder resume las noticias
   - Supervisor decide finalizar

### Ejemplo 2: Visualizar Sesión Antigua

```bash
# Iniciar solo dashboard
python run_with_dashboard.py --dashboard-only

# En el dashboard:
# 1. Sidebar → "Cargar desde archivo"
# 2. Ruta: .runs/2025-10-25_20-30-15/events.jsonl
# 3. Click "Cargar archivo"
```

### Ejemplo 3: Usar EnhancedRecorder Directamente

```python
from coreee.enhanced_recorder import create_recorder
from coreee.event_bus import get_event_bus

# Crear recorder mejorado
recorder = create_recorder(".runs/test", session_id="test123", use_enhanced=True)

# Emitir eventos (se ven en el dashboard en tiempo real)
recorder.emit_session_start(turn=0, task="Test task")
recorder.emit_user_message(turn=1, content="Hola sistema")
recorder.emit_coder_message(turn=2, content="Procesando...", action="thinking")
recorder.emit_tool_creation(turn=3, tool_name="test_tool", code="def test(): pass")
recorder.emit_session_end(turn=4, status="completed", summary="Test exitoso")
```

### Ejemplo 4: Suscribirse al EventBus

```python
from coreee.event_bus import get_event_bus

bus = get_event_bus()

# Listener personalizado
def my_custom_listener(event):
    if event.etype == "tool_created":
        print(f"🔧 Nueva herramienta: {event.tool_name}")
        # Enviar notificación, guardar a DB, etc.

bus.subscribe(my_custom_listener)

# Ahora my_custom_listener recibirá todos los eventos
```

---

## 🎯 Casos de Uso

### 1. Debugging en Tiempo Real

Ver exactamente qué está haciendo el sistema:
- ¿Qué herramienta falló?
- ¿Qué argumentos recibió?
- ¿Cuál fue el error exacto?

### 2. Monitoreo de Ejecución Larga

Para tareas que toman mucho tiempo:
- Ver progreso en tiempo real
- Detectar si el sistema está "colgado"
- Ver en qué paso está actualmente

### 3. Análisis Post-Mortem

Cargar sesiones antiguas y analizar:
- ¿Por qué falló esta sesión?
- ¿Qué herramientas se crearon?
- ¿Cuál fue el flujo de ejecución?

### 4. Demos y Presentaciones

Mostrar el sistema funcionando:
- Vista profesional y limpia
- Actualización en tiempo real
- Fácil de entender para no técnicos

### 5. Desarrollo y Testing

Al desarrollar nuevas funcionalidades:
- Ver eventos que emite tu código
- Verificar que los eventos tienen los datos correctos
- Debugging visual

---

## 🔧 Personalización

### Cambiar Intervalo de Refresh

En el sidebar del dashboard:
```
Auto-refresh: ☑️
Intervalo: ⚫━━━━━━━ 2 segundos
```

### Agregar Filtros Personalizados

Editar `dashboard_streamlit.py`:

```python
# Filtro por session_id
filter_session = st.text_input("Session ID", "")
if filter_session:
    filtered_events = [e for e in filtered_events if e.session_id == filter_session]
```

### Agregar Nueva Visualización

En `dashboard_streamlit.py`, agregar nuevo tab:

```python
tab6 = st.tabs(["...", "...", "🆕 Mi Tab"])

with tab6:
    st.header("🆕 Mi Visualización")
    # Tu código aquí
```

### Cambiar Colores y Estilos

En `dashboard_streamlit.py`, modificar el CSS:

```python
st.markdown("""
<style>
    .event-coder {
        border-left-color: #ff0000;  /* Rojo en vez de verde */
        background-color: #ffeeee;
    }
</style>
""", unsafe_allow_html=True)
```

---

## 🚨 Troubleshooting

### Dashboard no se abre automáticamente

**Síntoma:** Dashboard no inicia con `run_with_dashboard.py`

**Soluciones:**
1. Instalar Streamlit: `pip install streamlit`
2. Iniciar manualmente: `streamlit run dashboard_streamlit.py`
3. Usar `--no-dashboard` y abrir manualmente

### No aparecen eventos en el dashboard

**Causas posibles:**

1. **Sistema no usa EnhancedRecorder**
   ```python
   # Verificar que se usa EnhancedRecorder
   from coreee.enhanced_recorder import EnhancedRecorder
   recorder = EnhancedRecorder(...)  # No Recorder()
   ```

2. **Auto-refresh desactivado**
   - En el sidebar, activar "Auto-refresh"

3. **Filtros muy restrictivos**
   - Verificar filtros en sidebar
   - Asegurar que todos los roles están seleccionados

### Dashboard se actualiza muy lento

**Solución:** Reducir intervalo de refresh
```
Intervalo: ⚫━━━━━━━ 1 segundo
```

### Puerto 8501 ya en uso

**Síntoma:** Error al iniciar Streamlit

**Solución:**
```bash
# Matar proceso en el puerto
# Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8501 | xargs kill -9

# O usar otro puerto
streamlit run dashboard_streamlit.py --server.port 8502
```

---

## 📊 Performance

### Historial en Memoria

El EventBus mantiene los últimos **1000 eventos** en memoria para acceso rápido.

Eventos más antiguos se descartan automáticamente pero permanecen en el archivo `.jsonl`.

### Auto-Refresh

Con auto-refresh activado, el dashboard se recarga cada N segundos.

Para sesiones largas, considera:
- Aumentar intervalo (5-10 segundos)
- Desactivar auto-refresh y refrescar manualmente (F5)

### Archivos Grandes

Para sesiones con muchos eventos (>10,000):
- El dashboard carga solo desde EventBus (últimos 1000)
- Para ver más, usa "Cargar desde archivo" y filtra por rango de tiempo

---

## 🎓 Mejores Prácticas

### 1. Usa EnhancedRecorder Siempre

```python
# ✅ Bueno
from coreee.enhanced_recorder import create_recorder
recorder = create_recorder(root, session_id, use_enhanced=True)

# ❌ Malo (no emite a EventBus)
from coreee.timeline_recorder import Recorder
recorder = Recorder(root)
```

### 2. Emite Eventos Descriptivos

```python
# ✅ Bueno
recorder.emit(
    turn=1,
    role="coder",
    etype="tool_created",
    summary="Creada herramienta fetch_news para obtener noticias",
    data={"tool_name": "fetch_news", "code": code}
)

# ❌ Malo (poco descriptivo)
recorder.emit(turn=1, role="coder", etype="event", summary="algo")
```

### 3. Mantén Dashboard Abierto Durante Ejecución

Para ver eventos en tiempo real, inicia el dashboard **antes** de ejecutar el sistema.

### 4. Guarda Sesiones Importantes

Los eventos en memoria se pierden al cerrar el dashboard. Para preservarlos:
- Los archivos `.jsonl` son permanentes
- Usa "Cargar desde archivo" para revisitar

---

## 🔗 Archivos Creados

1. **`coreee/event_bus.py`** - Bus de eventos centralizado
2. **`coreee/enhanced_recorder.py`** - Recorder con broadcasting
3. **`dashboard_streamlit.py`** - Dashboard Streamlit
4. **`run_with_dashboard.py`** - Script de inicio
5. **`REALTIME_DASHBOARD.md`** - Esta documentación

---

## 🎉 Conclusión

El sistema de visualización en tiempo real está **completamente funcional** y listo para usar.

**Próximos pasos:**
1. `pip install streamlit pandas`
2. `python run_with_dashboard.py -q "tu tarea"`
3. Abre http://localhost:8501
4. ¡Disfruta visualizando todo en tiempo real! 🚀

---

**¿Preguntas?** Revisa esta documentación o abre un issue.
