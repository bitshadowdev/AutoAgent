# ✅ Solución - Dashboard Funcionando

## Problema Resuelto

El dashboard no mostraba eventos porque:
1. ❌ Streamlit corre en proceso separado → EventBus en memoria no se comparte
2. ✅ **Solución**: Dashboard ahora lee automáticamente el archivo `events.jsonl` más reciente

---

## 🚀 Cómo Usar Ahora

### Opción 1: Automático (Recomendado)

```bash
python run_with_dashboard.py -q "tu tarea aquí"
```

**Qué hace:**
1. Inicia dashboard en background
2. Ejecuta tu tarea
3. Dashboard carga automáticamente `.runs/<última-sesión>/events.jsonl`
4. **Auto-refresh cada 2 segundos** - ves eventos aparecer en tiempo real

### Opción 2: Manual (Dos Terminales)

**Terminal 1:**
```bash
streamlit run dashboard_streamlit.py
```

**Terminal 2:**
```bash
python coreee/sistema_agentes_supervisor_coder.py -q "tu tarea"
```

Dashboard detecta y carga automáticamente el `events.jsonl` más reciente.

---

## 📊 Qué Verás Ahora

### 1. Header con Origen de Datos
```
📁 Cargando eventos desde: `.runs/2025-10-26_13-20-15/events.jsonl`
```

### 2. Métricas Actualizándose
```
📊 Total Eventos: 25    👂 Listeners: 0    🎯 Sesiones: 1    ⏱️ Último: 13:45:23
```

### 3. Timeline con Eventos
- Mensajes del usuario
- Acciones del Coder
- Herramientas creadas
- Resultados de herramientas
- Decisiones del Supervisor

### 4. Código de Herramientas
Con syntax highlighting y número de líneas

### 5. Estadísticas y Gráficos
Actualizándose en cada refresh

---

## ⚙️ Configuración en Sidebar

### Auto-Refresh
```
☑️ Auto-refresh
Intervalo: ⚫━━━━━━━ 2 segundos
```

**Recomendado**: Activado con 2 segundos

### Si NO Ves Eventos

1. **Verifica que auto-refresh está ON** en el sidebar
2. **Espera 2 segundos** - el dashboard se recarga automáticamente
3. **Verifica que la tarea está corriendo** en la otra terminal

---

## 🧪 Test Rápido

### Probar que Funciona:

**Terminal 1:**
```bash
streamlit run dashboard_streamlit.py
```

**Terminal 2:**
```bash
python coreee/sistema_agentes_supervisor_coder.py -q "Crea una herramienta que sume 2 y 3"
```

**En Dashboard:**
- Espera 2-5 segundos
- Deberías ver aparecer eventos
- Header muestra: `📁 Cargando eventos desde: .runs/...`

---

## 🔍 Troubleshooting

### "No hay eventos para mostrar"

**Causa 1: Sistema no ha generado eventos aún**
- Espera a que la tarea empiece a ejecutarse

**Causa 2: Auto-refresh desactivado**
- Activa "Auto-refresh" en el sidebar

**Causa 3: No hay archivo events.jsonl**
- Verifica que existe `.runs/<alguna-carpeta>/events.jsonl`
- Ejecuta una tarea primero

### Dashboard carga archivo viejo

**Solución**: En el sidebar:
- "Cargar desde archivo"
- Especifica ruta exacta: `.runs/2025-10-26_13-20-15/events.jsonl`
- Click "Cargar archivo"

### Eventos no se actualizan

**Verifica**:
- ✅ Auto-refresh está ON
- ✅ Sistema está ejecutando (no ha terminado)
- ✅ Archivo events.jsonl está creciendo

**Forzar refresh**: Presiona `R` en el navegador

---

## 🎯 Casos de Uso

### Ver Sesión en Ejecución (Tiempo Real)

1. Inicia dashboard: `streamlit run dashboard_streamlit.py`
2. Inicia tarea: `python coreee/sistema_agentes_supervisor_coder.py -q "..."`
3. Ver eventos aparecer cada 2 segundos

### Ver Sesión Antigua (Post-Mortem)

1. Inicia dashboard: `streamlit run dashboard_streamlit.py`
2. En sidebar → "Cargar desde archivo"
3. Ruta: `.runs/2025-10-25_10-30-45/events.jsonl`
4. Click "Cargar archivo"

### Comparar Sesiones

Abre dos pestañas del dashboard y carga archivos diferentes en cada una.

---

## 💡 Tips

### 1. Mantén Auto-Refresh Activo
Para ver eventos en tiempo real mientras el sistema ejecuta.

### 2. Usa Filtros
Si hay muchos eventos:
- Filtrar por rol (user, coder, supervisor, etc.)
- Filtrar por tipo de evento (regex)

### 3. Tab "Inspector"
Para ver detalles JSON completos de cualquier evento.

### 4. Tab "Herramientas"
Para ver el código completo con syntax highlighting.

---

## ✅ Cambios Implementados

1. **Dashboard lee archivos** en vez de EventBus en memoria
2. **Detección automática** del archivo más reciente
3. **Auto-reload** del mismo archivo con auto-refresh
4. **Indicador de origen** en el header
5. **Compatible** con sesiones antiguas

---

## 🎉 Resultado

**Dashboard 100% funcional** que:
- ✅ Detecta automáticamente nuevas sesiones
- ✅ Carga eventos del archivo más reciente
- ✅ Se actualiza cada 2 segundos
- ✅ Muestra todos los eventos: mensajes, código, stats

**Pruébalo ahora:**
```bash
python run_with_dashboard.py -q "Crea una calculadora simple"
```

Abre http://localhost:8501 y disfruta la visualización en tiempo real! 🚀
