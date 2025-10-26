# ✅ Dashboard Arreglado - Detecta Sesiones Nuevas Automáticamente

## 🎯 Problema Resuelto

**Antes:**
- Dashboard se iniciaba → Encontraba archivo **viejo**
- Sistema creaba archivo **NUEVO**
- Dashboard seguía mostrando el **viejo** ❌

**Ahora:**
- Dashboard en **modo auto-detección** → Busca archivo **MÁS reciente** en cada refresh
- Detecta automáticamente cuando hay una **sesión nueva**
- Cambia al archivo nuevo **automáticamente** ✅

---

## 🔄 Dos Modos de Operación

### Modo 1: Auto-Detección (Por Defecto) 🔄

**Comportamiento:**
- Busca el archivo MÁS reciente en cada refresh (cada 2 segundos)
- Si detecta una sesión nueva, cambia automáticamente
- Muestra notificación: `🆕 Detectada nueva sesión: ...`

**Header muestra:**
```
🔄 AUTO-DETECT | Cargando eventos desde: `.runs/2025-10-26_13-25-30/events.jsonl`
```

**Ideal para:**
- Ver sesiones en tiempo real
- Ejecutar múltiples tareas y ver la más reciente siempre

### Modo 2: Fijo (Manual) 📌

**Comportamiento:**
- Lee solo del archivo especificado
- NO cambia a sesiones nuevas automáticamente
- Ideal para analizar una sesión específica

**Header muestra:**
```
📌 FIJO | Cargando eventos desde: `.runs/2025-10-25_10-30-00/events.jsonl`
```

**Activar:**
1. Sidebar → "Cargar archivo específico"
2. Especifica ruta: `.runs/2025-10-25_10-30-00/events.jsonl`
3. Click "📂 Cargar archivo específico"

**Volver a auto-detección:**
- Click botón "🔄 Auto-detectar" en el sidebar

---

## 🚀 Uso Recomendado

### Para Ver Nuevas Sesiones en Tiempo Real

```bash
# Terminal 1: Iniciar dashboard
streamlit run dashboard_streamlit.py

# Esperar 2-3 segundos a que cargue

# Terminal 2: Ejecutar tarea
python run_with_dashboard.py -q "tu tarea aquí"
```

**Qué verás:**
1. Dashboard inicia en modo auto-detección
2. Muestra "💾 Esperando eventos..."
3. Ejecutas tarea → Sistema crea `.runs/2025-10-26_13-26-00/`
4. En el siguiente refresh (2 segundos) → Dashboard detecta el nuevo archivo
5. Muestra notificación: `🆕 Detectada nueva sesión: ...`
6. Eventos aparecen automáticamente

### Para Ejecutar Múltiples Tareas

```bash
# Dashboard ya está corriendo

# Terminal 2: Tarea 1
python coreee/sistema_agentes_supervisor_coder.py -q "tarea 1"

# Esperar a que termine

# Terminal 2: Tarea 2
python coreee/sistema_agentes_supervisor_coder.py -q "tarea 2"

# Dashboard cambia automáticamente a la tarea 2
```

Dashboard **siempre muestra la sesión más reciente** en modo auto-detección.

---

## 🎛️ Controles en el Sidebar

### Gestión de Archivos

```
📁 Gestión de Archivos
─────────────────────────────
[🔄 Auto-detectar] [📊 Refrescar]
─────────────────────────────
Ruta manual: .runs/2025-10-26.../events.jsonl
        [📂 Cargar archivo específico]

📄 Archivo actual:
.runs/2025-10-26_13-26-00/events.jsonl
```

**Botones:**

- **🔄 Auto-detectar**: Vuelve al modo auto-detección (busca siempre el más reciente)
- **📊 Refrescar**: Fuerza un refresh inmediato (sin esperar 2 segundos)
- **📂 Cargar archivo específico**: Carga un archivo particular y activa modo fijo

---

## 📊 Indicadores Visuales

### Header - Modo Actual

**Auto-detección:**
```
🔄 AUTO-DETECT | Cargando eventos desde: .runs/2025-10-26_13-26-00/events.jsonl
```

**Fijo:**
```
📌 FIJO | Cargando eventos desde: .runs/2025-10-25_10-30-00/events.jsonl
```

**Sin eventos:**
```
💾 Esperando eventos... (Modo auto-detección)
```

### Notificaciones

**Nueva sesión detectada:**
```
✅ 🆕 Detectada nueva sesión: `.runs/2025-10-26_13-26-15/events.jsonl`
```

**Modo auto-detección activado:**
```
✅ Modo auto-detección activado
```

---

## 🧪 Test del Fix

### Test 1: Detección Automática de Nueva Sesión

```bash
# 1. Iniciar dashboard
streamlit run dashboard_streamlit.py

# 2. Observar: "💾 Esperando eventos..."

# 3. En otra terminal, ejecutar tarea
python coreee/sistema_agentes_supervisor_coder.py -q "test 1"

# 4. En máximo 2 segundos, dashboard debería mostrar:
#    🆕 Detectada nueva sesión: .runs/2025-10-26_XX-XX-XX/events.jsonl
#    🔄 AUTO-DETECT | Cargando eventos desde: ...

# 5. Ejecutar otra tarea
python coreee/sistema_agentes_supervisor_coder.py -q "test 2"

# 6. Dashboard cambia automáticamente a la nueva sesión
```

✅ **Resultado esperado**: Dashboard siempre muestra la sesión **más reciente**

### Test 2: Modo Fijo

```bash
# 1. Dashboard corriendo

# 2. Sidebar → "Cargar archivo específico"
#    Ruta: .runs/2025-10-25_10-00-00/events.jsonl
#    Click "Cargar archivo"

# 3. Header muestra: 📌 FIJO | ...

# 4. Ejecutar nueva tarea
python coreee/sistema_agentes_supervisor_coder.py -q "nueva tarea"

# 5. Dashboard NO cambia (sigue en modo fijo)

# 6. Click "🔄 Auto-detectar"

# 7. Dashboard cambia a la sesión más reciente
```

✅ **Resultado esperado**: Modo fijo mantiene el archivo, auto-detectar cambia al más reciente

---

## ⚙️ Configuración Recomendada

### Para Desarrollo/Debugging

```
☑️ Auto-refresh: ON
Intervalo: 2 segundos
Modo: 🔄 AUTO-DETECT
```

### Para Análisis de Sesión Específica

```
☐ Auto-refresh: OFF (opcional)
Modo: 📌 FIJO
Archivo: (la sesión que quieres analizar)
```

---

## 🎯 Flujo Típico

### Escenario: Ejecutar Varias Tareas y Ver Eventos

1. **Iniciar dashboard**
   ```bash
   streamlit run dashboard_streamlit.py
   ```

2. **Verificar modo**
   - Header debe mostrar "💾 Esperando eventos... (Modo auto-detección)"

3. **Ejecutar tarea 1**
   ```bash
   python coreee/sistema_agentes_supervisor_coder.py -q "tarea 1"
   ```

4. **Observar dashboard**
   - En 2 segundos: `🆕 Detectada nueva sesión`
   - Eventos de tarea 1 aparecen
   - Header: `🔄 AUTO-DETECT | ...`

5. **Ejecutar tarea 2**
   ```bash
   python coreee/sistema_agentes_supervisor_coder.py -q "tarea 2"
   ```

6. **Dashboard cambia automáticamente**
   - `🆕 Detectada nueva sesión: ...`
   - Ahora muestra eventos de tarea 2

7. **Revisar tarea 1 anterior**
   - Sidebar → "Cargar archivo específico"
   - Especificar ruta de tarea 1
   - Click "Cargar"
   - Dashboard cambia a tarea 1 (modo fijo)

8. **Volver a ver la más reciente**
   - Click "🔄 Auto-detectar"
   - Dashboard vuelve a tarea 2

---

## 💡 Tips

### 1. Usa Auto-Detección por Defecto
Deja el dashboard en modo auto-detección para ver siempre la sesión más reciente.

### 2. Fija para Análisis Profundo
Si quieres analizar una sesión específica sin distracciones, cárgala manualmente y desactiva auto-refresh.

### 3. Dos Dashboards Simultáneos
Abre dos pestañas del navegador:
- Una en auto-detección (para sesiones nuevas)
- Otra en modo fijo (para analizar una sesión vieja)

### 4. Usa Filtros
Con auto-refresh activo y muchos eventos, usa filtros por rol o tipo para ver solo lo relevante.

---

## 🎉 Resumen

**Problema original**: Dashboard mostraba sesión vieja cuando se iniciaba antes que el sistema.

**Solución implementada**:
- ✅ Modo auto-detección busca archivo más reciente en cada refresh
- ✅ Detecta automáticamente nuevas sesiones
- ✅ Notifica cuando cambia de sesión
- ✅ Modo fijo para análisis de sesiones específicas
- ✅ Botones para cambiar entre modos

**Resultado**: Dashboard **siempre** muestra la sesión correcta en modo auto-detección 🚀

---

**¡Pruébalo ahora!**
```bash
streamlit run dashboard_streamlit.py
```

Y ejecuta:
```bash
python run_with_dashboard.py -q "test de detección automática"
```

En 2 segundos verás la nueva sesión aparecer automáticamente! ✨
