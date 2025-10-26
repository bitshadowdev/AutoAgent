# AutoAgent - Sistema de Agentes con Persistencia

Sistema de agentes inteligentes (Supervisor + Coder) con **persistencia completa** de herramientas y sesiones.

## 🚀 Características Principales

### ✅ Persistencia de Herramientas
- Las herramientas creadas se guardan automáticamente en disco (`.permanent_tools/`)
- Se cargan automáticamente en cada ejecución
- Versionado y timestamps de creación/actualización
- Manifest JSON con metadatos de cada herramienta

### ✅ Persistencia de Sesiones
- Guarda automáticamente el historial de conversación
- Continúa sesiones anteriores donde las dejaste
- Gestiona múltiples sesiones simultáneamente
- Exporta/importa sesiones en formato JSON

### ✅ Sistema de Agentes
- **Coder**: Agente programador que crea y ejecuta herramientas Python
- **Supervisor**: Evalúa resultados y decide próximos pasos
- Modo abierto: permite imports, acceso a red, sistema de archivos, etc.

### ✅ Agentes Dinámicos (NUEVO 🤖)
- **Creación de agentes especializados** durante la ejecución
- **Coder y Supervisor** pueden crear nuevos agentes para tareas específicas
- **Persistencia automática** de agentes en disco (`.agents/`)
- **Reutilización** de agentes entre sesiones
- **Colaboración multi-agente** para tareas complejas
- Ejemplos: `data_analyst`, `ux_designer`, `security_auditor`
- Ver guía completa en [AGENTES_DINAMICOS.md](AGENTES_DINAMICOS.md)

### ✅ Auto-corrección con Retry Inteligente
- **Detección automática de errores** con sugerencias específicas
- **Actualización de herramientas** con el mismo nombre cuando fallan
- **Feedback iterativo** del Supervisor con tips accionables
- **Corrección progresiva** hasta resolver el problema
- **10 turnos por defecto** para permitir múltiples correcciones
- Ver detalles en [MEJORAS_RETRY.md](MEJORAS_RETRY.md)

## 📋 Requisitos

- Python 3.9+
- Cloudflare Workers AI (cuenta y tokens)

## 🔧 Instalación

1. **Clonar el repositorio**
```bash
git clone <repo-url>
cd AutoAgent
```

2. **Crear entorno virtual**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirement.txt
```

4. **Configurar variables de entorno**

Crear archivo `.env` en la raíz del proyecto:
```env
CLOUDFLARE_ACCOUNT_ID=tu_account_id
CLOUDFLARE_AUTH_TOKEN=tu_auth_token
CF_MODEL=@cf/openai/gpt-oss-120b
TOOL_STORE_DIR=.permanent_tools
```

## 💻 Uso Básico

### Ejecutar una tarea

```bash
cd coreee
python sistema_agentes_supervisor_coder.py -q "tu tarea aquí"
```

### Con session ID personalizado

```bash
python sistema_agentes_supervisor_coder.py -q "crear una calculadora" --session-id mi_calculadora
```

### Reanudar una sesión anterior

```bash
python sistema_agentes_supervisor_coder.py --session-id mi_calculadora --resume
```

## 📊 Gestión de Sesiones

### Listar todas las sesiones

```bash
python manage_sessions.py list
```

### Filtrar sesiones por estado

```bash
python manage_sessions.py list --status completed
python manage_sessions.py list --status active
```

### Ver detalles de una sesión

```bash
python manage_sessions.py show SESSION_ID
```

### Exportar sesión

```bash
python manage_sessions.py export SESSION_ID --output backup.json
```

### Importar sesión

```bash
python manage_sessions.py import backup.json
```

### Eliminar sesión

```bash
python manage_sessions.py delete SESSION_ID
```

### Limpiar sesiones antiguas

```bash
# Eliminar sesiones completadas
python manage_sessions.py clean --status completed

# Eliminar sesiones de más de 30 días
python manage_sessions.py clean --days 30
```

## 🛠️ Gestión de Herramientas

### Listar herramientas persistentes

```bash
python sistema_agentes_supervisor_coder.py --tools-list
```

### Cambiar directorio de herramientas

```bash
python sistema_agentes_supervisor_coder.py --tools-dir /ruta/custom -q "tarea"
```

## 🤖 Gestión de Agentes Dinámicos

### Listar agentes creados

```bash
python sistema_agentes_supervisor_coder.py --agents-list
```

### Ejemplo de uso: Crear un agente analista

```bash
python sistema_agentes_supervisor_coder.py -q "Analiza el archivo datos.csv y genera insights" --session-id analisis
```

El Coder automáticamente creará un agente `data_analyst` si lo necesita.

### Cambiar directorio de agentes

```bash
python sistema_agentes_supervisor_coder.py --agents-dir /ruta/custom -q "tarea"
```

## 📁 Estructura del Proyecto

```
AutoAgent/
├── coreee/
│   ├── sistema_agentes_supervisor_coder.py  # Sistema principal
│   ├── session_manager.py                   # Gestión de sesiones
│   ├── agent_registry.py                    # Registro de agentes dinámicos
│   ├── manage_sessions.py                   # CLI para sesiones
│   ├── llm_client.py                        # Cliente LLM
│   └── timeline_recorder.py                 # Grabación de eventos
├── .permanent_tools/                         # Herramientas persistentes
│   ├── manifest.json                        # Metadatos de herramientas
│   └── *.py                                 # Archivos de herramientas
├── .agents/                                  # Agentes dinámicos
│   ├── manifest.json                        # Índice de agentes
│   └── *.json                               # Definiciones de agentes
├── .sessions/                                # Sesiones persistentes
│   ├── index.json                           # Índice de sesiones
│   └── *.json                               # Datos de sesiones
├── .runs/                                    # Logs de ejecución
│   └── YYYY-MM-DD_HH-MM-SS/
│       ├── events.jsonl                     # Eventos en formato JSONL
│       ├── timeline.md                      # Timeline en Markdown
│       ├── timeline.html                    # Timeline en HTML
│       └── transcript.json                  # Transcripción completa
├── .env                                      # Variables de entorno
└── README.md                                 # Este archivo
```

## 🔐 Seguridad

⚠️ **IMPORTANTE**: Este sistema funciona en "modo abierto", permitiendo:
- Imports arbitrarios
- Acceso a red (HTTP/HTTPS)
- Sistema de archivos
- Ejecución de subprocesos (pip, etc.)

**Úsalo solo en entornos controlados y de confianza.**

## 📖 Ejemplos de Uso

### Ejemplo 1: Crear y persistir herramienta

```bash
python sistema_agentes_supervisor_coder.py -q "Crea una herramienta para scrapear noticias de un sitio web" --session-id scraper_news
```

La herramienta se guardará automáticamente y estará disponible en futuras ejecuciones.

### Ejemplo 2: Continuar trabajo anterior

```bash
# Primera sesión
python sistema_agentes_supervisor_coder.py -q "Analiza el archivo datos.csv" --session-id analisis_datos

# Días después, continuar
python sistema_agentes_supervisor_coder.py --session-id analisis_datos --resume
```

### Ejemplo 3: Gestión avanzada

```bash
# Ver sesiones activas
python manage_sessions.py list --status active

# Ver detalles de una sesión
python manage_sessions.py show analisis_datos

# Exportar para backup
python manage_sessions.py export analisis_datos --output backup_analisis.json

# Limpiar sesiones completadas antiguas
python manage_sessions.py clean --status completed --days 30
```

## 🔄 Flujo de Trabajo

1. **Inicio**: El sistema carga automáticamente herramientas persistentes
2. **Ejecución**: 
   - El Coder crea/usa herramientas según la tarea
   - El Supervisor evalúa y dirige
   - El progreso se guarda automáticamente cada turno
3. **Finalización**: La sesión se marca como "completed" y se guarda

## ⚙️ Configuración Avanzada

### Variables de Entorno Opcionales

```env
# Modelo LLM a usar
CF_MODEL=@cf/openai/gpt-oss-120b

# Directorio de herramientas
TOOL_STORE_DIR=.permanent_tools

# Tamaño máximo de código de herramientas (caracteres)
TOOL_CODE_MAX_CHARS=200000

# Habilitar/deshabilitar herramientas peligrosas
DANGEROUS_TOOLS=1
```

### Argumentos CLI Disponibles

```bash
# Sistema principal
-q, --task              : Tarea a resolver
-m, --max-turns         : Máximo de turnos (default: 5)
--log-dir               : Directorio para logs (default: .runs)
--session-id            : ID de sesión
--resume                : Reanudar sesión
--sessions-list         : Listar sesiones
--sessions-dir          : Directorio de sesiones (default: .sessions)
--delete-session        : Eliminar sesión
--tools-list            : Listar herramientas
--tools-dir             : Directorio de herramientas (default: .permanent_tools)
```

## 🐛 Troubleshooting

### Error: No se encuentran las credenciales de Cloudflare

Verifica que `.env` existe y contiene `CLOUDFLARE_ACCOUNT_ID` y `CLOUDFLARE_AUTH_TOKEN`.

### Error: No se puede cargar la sesión

Verifica que el `session_id` es correcto usando:
```bash
python manage_sessions.py list
```

### Las herramientas no se cargan

Verifica que el directorio `.permanent_tools/` existe y contiene `manifest.json`.

## 📝 Notas

- Las sesiones se guardan automáticamente después de cada turno
- Las herramientas creadas persisten indefinidamente hasta que se eliminen manualmente
- El sistema detecta automáticamente herramientas .py en el directorio incluso si no están en el manifest
- Los logs completos de cada ejecución se guardan en `.runs/`

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver `LICENSE` para más detalles.

## 🙏 Agradecimientos

- Cloudflare Workers AI por la infraestructura LLM
- Comunidad Python por las excelentes herramientas
