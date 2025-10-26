# 🚀 Guía Rápida - AutoAgent con Persistencia

## Inicio Rápido (5 minutos)

### 1. Configuración inicial

```bash
# Activar entorno virtual
venv\Scripts\activate

# Ir al directorio de trabajo
cd coreee
```

### 2. Primera ejecución

```bash
# Ejecutar una tarea simple
python sistema_agentes_supervisor_coder.py -q "Crea una función que calcule el factorial de un número"
```

El sistema creará automáticamente:
- Directorio `.permanent_tools/` para herramientas
- Directorio `.sessions/` para sesiones
- Directorio `.runs/` para logs

### 3. Ver herramientas creadas

```bash
python sistema_agentes_supervisor_coder.py --tools-list
```

---

## Comandos Esenciales

### 📝 Crear y guardar sesión con nombre

```bash
python sistema_agentes_supervisor_coder.py -q "tu tarea" --session-id nombre_sesion
```

### 🔄 Continuar sesión anterior

```bash
python sistema_agentes_supervisor_coder.py --session-id nombre_sesion --resume
```

### 📋 Ver todas las sesiones

```bash
python sistema_agentes_supervisor_coder.py --sessions-list
```

### 🔍 Gestión detallada de sesiones

```bash
# Listar todas
python manage_sessions.py list

# Ver detalles
python manage_sessions.py show nombre_sesion

# Eliminar sesión
python manage_sessions.py delete nombre_sesion
```

---

## Ejemplos Prácticos

### Ejemplo 1: Proyecto de scraping web

```bash
# Día 1: Crear el scraper
python sistema_agentes_supervisor_coder.py \
  -q "Crea una herramienta para scrapear titulares de noticias" \
  --session-id proyecto_scraper

# Día 2: Mejorar el scraper
python sistema_agentes_supervisor_coder.py \
  --session-id proyecto_scraper \
  --resume

# Ver qué herramientas se crearon
python sistema_agentes_supervisor_coder.py --tools-list
```

### Ejemplo 2: Análisis de datos

```bash
# Primera sesión
python sistema_agentes_supervisor_coder.py \
  -q "Analiza el archivo ventas.csv y genera estadísticas" \
  --session-id analisis_ventas

# Continuar después
python sistema_agentes_supervisor_coder.py \
  --session-id analisis_ventas \
  --resume
```

### Ejemplo 3: Exportar/Importar sesiones

```bash
# Exportar sesión importante
python manage_sessions.py export proyecto_scraper --output backup.json

# Importar en otra máquina
python manage_sessions.py import backup.json
```

---

## Estructura de Persistencia

```
AutoAgent/
├── .permanent_tools/          # ← Herramientas permanentes
│   ├── manifest.json          #    Metadatos de herramientas
│   └── scraper_news.py        #    Ejemplo de herramienta
│
├── .sessions/                 # ← Sesiones guardadas
│   ├── index.json             #    Índice de sesiones
│   └── proyecto_scraper.json  #    Datos de sesión
│
└── .runs/                     # ← Logs de ejecución
    └── 2025-01-15_10-30-45/
        ├── events.jsonl
        ├── timeline.md
        ├── timeline.html
        └── transcript.json
```

---

## Flujo de Trabajo Recomendado

### Para proyectos pequeños (tarea única)

```bash
# Sin especificar session-id (auto-generado)
python sistema_agentes_supervisor_coder.py -q "tarea simple"
```

### Para proyectos medianos (varias sesiones)

```bash
# Primera vez
python sistema_agentes_supervisor_coder.py -q "tarea" --session-id mi_proyecto

# Continuaciones
python sistema_agentes_supervisor_coder.py --session-id mi_proyecto --resume
```

### Para proyectos grandes (múltiples etapas)

```bash
# Etapa 1: Diseño
python sistema_agentes_supervisor_coder.py \
  -q "Diseña la arquitectura del sistema" \
  --session-id proyecto_fase1

# Etapa 2: Implementación
python sistema_agentes_supervisor_coder.py \
  -q "Implementa el módulo principal" \
  --session-id proyecto_fase2

# Etapa 3: Testing
python sistema_agentes_supervisor_coder.py \
  -q "Crea tests para el sistema" \
  --session-id proyecto_fase3

# Ver todas las fases
python manage_sessions.py list
```

---

## Mantenimiento

### Limpiar sesiones antiguas

```bash
# Sesiones completadas
python manage_sessions.py clean --status completed

# Sesiones de más de 30 días
python manage_sessions.py clean --days 30
```

### Backup de todo el proyecto

```bash
# Copiar directorios completos
xcopy .permanent_tools backup_tools\ /E /I
xcopy .sessions backup_sessions\ /E /I
```

### Ver logs de una ejecución específica

```bash
# Navegar a .runs/
cd ..\.runs

# Ver el timeline más reciente
dir /O-D
cd [carpeta_mas_reciente]
notepad timeline.md
```

---

## Tips y Trucos

### 💡 Reutilizar herramientas entre sesiones

Las herramientas creadas están disponibles automáticamente en todas las sesiones:

```bash
# Sesión 1: Crea herramienta
python sistema_agentes_supervisor_coder.py \
  -q "Crea una herramienta para validar emails" \
  --session-id crear_validador

# Sesión 2: Usa la herramienta
python sistema_agentes_supervisor_coder.py \
  -q "Usa la herramienta de validación de emails con test@example.com" \
  --session-id usar_validador
```

### 💡 Session IDs descriptivos

Usa nombres que describan el propósito:

```bash
# ✅ Bueno
--session-id scraper_amazon_precios
--session-id analisis_sentimientos_twitter
--session-id bot_discord_moderacion

# ❌ Evitar
--session-id session1
--session-id test
--session-id abc123
```

### 💡 Revisar progreso de sesión activa

```bash
python manage_sessions.py show nombre_sesion
```

Muestra:
- Cuántos turnos se han ejecutado
- Qué herramientas se usaron
- Estado actual (active/completed)
- Historial de mensajes

---

## Solución de Problemas Comunes

### ❌ "No se encuentra la sesión"

```bash
# Verificar sesiones disponibles
python manage_sessions.py list

# Usar el session_id exacto
python sistema_agentes_supervisor_coder.py --session-id NOMBRE_EXACTO --resume
```

### ❌ "Error al cargar herramientas"

```bash
# Listar herramientas
python sistema_agentes_supervisor_coder.py --tools-list

# Si la lista está vacía, el directorio puede estar corrupto
# Eliminar y recrear
rmdir /S .permanent_tools
```

### ❌ Sesión no guarda el progreso

Verifica que especificaste `--session-id`:

```bash
# ✅ Correcto
python sistema_agentes_supervisor_coder.py -q "tarea" --session-id mi_sesion

# ❌ Sin guardar
python sistema_agentes_supervisor_coder.py -q "tarea"
```

---

## Comandos de Referencia Rápida

```bash
# EJECUCIÓN
python sistema_agentes_supervisor_coder.py -q "tarea" --session-id NOMBRE
python sistema_agentes_supervisor_coder.py --session-id NOMBRE --resume

# LISTADOS
python sistema_agentes_supervisor_coder.py --tools-list
python sistema_agentes_supervisor_coder.py --sessions-list
python manage_sessions.py list
python manage_sessions.py list --status completed

# INSPECCIÓN
python manage_sessions.py show SESSION_ID

# MANTENIMIENTO
python manage_sessions.py delete SESSION_ID
python manage_sessions.py clean --days 30
python manage_sessions.py export SESSION_ID --output backup.json
python manage_sessions.py import backup.json

# CONFIGURACIÓN
python sistema_agentes_supervisor_coder.py --tools-dir /ruta/custom -q "tarea"
python sistema_agentes_supervisor_coder.py --sessions-dir /ruta/custom -q "tarea"
python sistema_agentes_supervisor_coder.py -m 10 -q "tarea"  # Max 10 turnos
```

---

## Próximos Pasos

1. **Experimenta** con tareas simples para familiarizarte
2. **Crea sesiones nombradas** para proyectos importantes
3. **Revisa los logs** en `.runs/` para entender el comportamiento
4. **Reutiliza herramientas** creadas en sesiones anteriores
5. **Exporta sesiones** importantes como backup

¡Ahora tienes persistencia completa de herramientas y agentes! 🎉
