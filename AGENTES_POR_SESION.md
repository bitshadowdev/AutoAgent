# Agentes por Sesión - Sistema de Equipos Aislados

**Fecha**: 26 Octubre 2025  
**Estado**: ✅ **IMPLEMENTADO**

---

## 🎯 Resumen

Los agentes dinámicos ahora son **específicos por sesión**, permitiendo crear diferentes "sistemas" o "equipos" de agentes especializados para cada proyecto.

### Antes ❌
- Todos los agentes eran **globales**
- Un solo directorio `.agents/` compartido
- Imposible tener equipos diferentes para proyectos distintos

### Ahora ✅
- Agentes **aislados por sesión**
- Estructura `.agents/{session_id}/`
- Cada sesión tiene su propio conjunto de agentes
- Equipos especializados por proyecto

---

## 📁 Nueva Estructura de Directorios

```
.agents/
├── global/                          # Sesión "global" (sin session-id)
│   ├── manifest.json
│   ├── data_analyst.json
│   └── fact_checker.json
│
├── proyecto_ml/                     # Sesión "proyecto_ml"
│   ├── manifest.json
│   ├── data_scientist.json
│   ├── model_trainer.json
│   └── performance_optimizer.json
│
├── ecommerce_app/                   # Sesión "ecommerce_app"
│   ├── manifest.json
│   ├── frontend_dev.json
│   ├── backend_dev.json
│   └── ux_designer.json
│
└── research_paper/                  # Sesión "research_paper"
    ├── manifest.json
    ├── researcher.json
    ├── writer.json
    └── reviewer.json
```

---

## 🚀 Cómo Usar

### 1. Crear Agentes en una Sesión Específica

```bash
# Sesión 1: Proyecto ML
python coreee/sistema_agentes_supervisor_coder.py \
  -q "Crea un agente data_scientist experto en ML" \
  --session-id proyecto_ml

# El agente se guarda en .agents/proyecto_ml/
```

```bash
# Sesión 2: Proyecto E-commerce (completamente independiente)
python coreee/sistema_agentes_supervisor_coder.py \
  -q "Crea un agente frontend_dev experto en React" \
  --session-id ecommerce_app

# El agente se guarda en .agents/ecommerce_app/
```

### 2. Listar Agentes de una Sesión

**Sesión específica:**
```bash
python coreee/sistema_agentes_supervisor_coder.py \
  --agents-list \
  --session-id proyecto_ml
```

Salida:
```
🤖 Agentes dinámicos de la sesión: proyecto_ml
Directorio: .agents/proyecto_ml

Nombre               Rol                            Capacidades
======================================================================================
data_scientist       Científico de Datos            machine learning, análisis...
model_trainer        Entrenador de Modelos          training, optimization...

Total: 2 agente(s) en esta sesión
```

**Sesión global (sin --session-id):**
```bash
python coreee/sistema_agentes_supervisor_coder.py --agents-list
```

Salida:
```
🤖 Agentes dinámicos de la sesión: global
Directorio: .agents/global

  (ningún agente creado aún en esta sesión)

💡 Hay agentes en otras sesiones: proyecto_ml, ecommerce_app
   Usa --agents-all-sessions para verlos todos
```

### 3. Ver Agentes de TODAS las Sesiones

```bash
python coreee/sistema_agentes_supervisor_coder.py --agents-all-sessions
```

Salida:
```
Agentes dinámicos por sesión (directorio base: .agents):

📁 Sesión: ecommerce_app (2 agente(s))
  Nombre             Rol                          Capacidades
  ==========================================================================================
  frontend_dev       Desarrollador Frontend       React, TypeScript...
  backend_dev        Desarrollador Backend        Node.js, API...

📁 Sesión: proyecto_ml (2 agente(s))
  Nombre             Rol                          Capacidades
  ==========================================================================================
  data_scientist     Científico de Datos          ML, análisis...
  model_trainer      Entrenador de Modelos        training, optimization...

📊 Total: 2 sesión(es) con agentes
```

### 4. Obtener Información Detallada de un Agente

```bash
python coreee/sistema_agentes_supervisor_coder.py \
  --agent-info data_scientist \
  --session-id proyecto_ml
```

### 5. Usar Agentes en una Sesión

```bash
# Los agentes solo están disponibles en su sesión
python coreee/sistema_agentes_supervisor_coder.py \
  -q "Analiza estos datos con técnicas avanzadas de ML" \
  --session-id proyecto_ml \
  --resume

# El Coder puede llamar a "data_scientist" o "model_trainer"
# porque están en la misma sesión
```

---

## 🔧 Cambios Técnicos Implementados

### 1. **AgentRegistry** Modificado

**Antes:**
```python
def __init__(self, llm, agents_dir: str = ".agents"):
    self.agents_dir = Path(agents_dir).resolve()
    # Todos los agentes en un solo directorio
```

**Ahora:**
```python
def __init__(self, llm, agents_base_dir: str = ".agents", session_id: Optional[str] = None):
    self.session_id = session_id or "global"
    self.agents_base_dir = Path(agents_base_dir).resolve()
    self.agents_dir = self.agents_base_dir / self.session_id  # Por sesión
```

**Nuevos métodos:**
- `switch_session(session_id)` - Cambia a otra sesión
- `list_all_sessions()` - Lista todas las sesiones con agentes
- `count_agents_by_session()` - Cuenta agentes por sesión

### 2. **MiniAgentSystem** Actualizado

```python
def run(self, task, session_id=None, ...):
    if session_id:
        self.current_session_id = session_id
        # 🆕 Cambiar AgentRegistry a esta sesión
        self.agents.switch_session(session_id)
```

### 3. **CLI Mejorado**

**Nuevos argumentos:**
- `--agents-all-sessions` - Ver agentes de todas las sesiones
- `--agents-list` ahora respeta `--session-id`

**Antes:**
```bash
# Solo mostraba todos los agentes mezclados
--agents-list
```

**Ahora:**
```bash
# Agentes de una sesión específica
--agents-list --session-id proyecto_ml

# Agentes de todas las sesiones (vista global)
--agents-all-sessions
```

---

## 📊 Casos de Uso

### Caso 1: Múltiples Proyectos Independientes

```bash
# Proyecto A: Sistema de recomendaciones
python sistema_agentes_supervisor_coder.py \
  -q "Crea agentes para sistema de recomendaciones" \
  --session-id recommender_system

# Proyecto B: Chatbot de soporte
python sistema_agentes_supervisor_coder.py \
  -q "Crea agentes para chatbot de soporte técnico" \
  --session-id support_chatbot

# Los agentes están completamente aislados
```

### Caso 2: Equipos Especializados por Tarea

**Research & Development:**
```bash
--session-id research_ai
# Agentes: researcher, paper_writer, code_reviewer
```

**Production Deployment:**
```bash
--session-id production_ops
# Agentes: devops_engineer, security_auditor, performance_optimizer
```

**Customer Facing:**
```bash
--session-id customer_support
# Agentes: support_agent, escalation_handler, feedback_analyzer
```

### Caso 3: Entornos (Dev, Staging, Prod)

```bash
# Desarrollo
--session-id dev_environment
# Agentes experimentales, prototipos

# Staging
--session-id staging_environment
# Agentes probados, pre-producción

# Producción
--session-id prod_environment
# Agentes validados, estables
```

---

## 🔄 Migración de Agentes Existentes

Si ya tenías agentes en el sistema antiguo (`.agents/` global):

### Opción 1: Mantenerlos en "global"
Los agentes existentes quedarán en `.agents/` y se accederán sin `--session-id`.

### Opción 2: Moverlos manualmente a una sesión
```bash
# Mover agentes antiguos a una sesión específica
mkdir .agents/mi_proyecto
mv .agents/*.json .agents/mi_proyecto/
mv .agents/manifest.json .agents/mi_proyecto/
```

### Opción 3: Recrearlos por sesión
Dejar los agentes viejos y crear nuevos específicos para cada sesión.

---

## 💡 Mejores Prácticas

### 1. **Naming de Sesiones**
- Usa nombres descriptivos: `ml_research`, `web_app`, `data_pipeline`
- Evita espacios: usa guiones bajos o kebab-case
- Sé consistente con la convención

### 2. **Organización de Agentes**
```
Sesión: full_stack_project
├── frontend_dev      → React, CSS, UX
├── backend_dev       → API, database, auth
├── qa_tester         → testing, bugs
└── project_manager   → planning, coordination
```

### 3. **Gestión de Sesiones**
```bash
# Ver qué sesiones tienes
--agents-all-sessions

# Ver agentes de una sesión antes de trabajar
--agents-list --session-id {nombre}

# Limpiar sesiones viejas
rm -rf .agents/old_project
```

### 4. **Reutilización**
Si necesitas el **mismo agente en múltiples sesiones**, créalo en cada una:
```bash
# No puedes "compartir" agentes entre sesiones
# Pero puedes recrear el mismo agente con el mismo prompt
```

---

## ⚠️ Notas Importantes

1. **Sin session-id = "global"**
   - Si no especificas `--session-id`, usa la sesión "global"
   - `.agents/global/`

2. **Agentes NO se comparten**
   - Cada sesión tiene sus propios agentes
   - No hay forma de "importar" agentes de otra sesión
   - Esto es **por diseño** para aislamiento total

3. **Resume respeta la sesión**
   - Al usar `--resume`, los agentes de esa sesión se cargan automáticamente
   - No necesitas especificar nada extra

4. **Eliminar sesión NO elimina agentes**
   - Si borras una sesión con `--delete-session`, los agentes permanecen en `.agents/{session_id}/`
   - Debes eliminar el directorio manualmente si quieres borrarlos

---

## 🧪 Testing

### Probar el sistema de agentes por sesión:

```bash
# 1. Crear agente en sesión A
python coreee/sistema_agentes_supervisor_coder.py \
  -q "Crea un agente test_agent_A" \
  --session-id sesion_a

# 2. Crear agente en sesión B
python coreee/sistema_agentes_supervisor_coder.py \
  -q "Crea un agente test_agent_B" \
  --session-id sesion_b

# 3. Verificar aislamiento
python coreee/sistema_agentes_supervisor_coder.py \
  --agents-list --session-id sesion_a
# Solo debe mostrar test_agent_A

python coreee/sistema_agentes_supervisor_coder.py \
  --agents-list --session-id sesion_b
# Solo debe mostrar test_agent_B

# 4. Ver todas las sesiones
python coreee/sistema_agentes_supervisor_coder.py --agents-all-sessions
# Debe mostrar ambas sesiones con sus agentes

# 5. Limpiar
rm -rf .agents/sesion_a .agents/sesion_b
```

---

## 📝 Ejemplo Completo: Pipeline de Datos

```bash
# Paso 1: Crear sesión de data pipeline
python coreee/sistema_agentes_supervisor_coder.py \
  -q "Crea estos agentes:
       1. data_ingester: experto en ETL y APIs
       2. data_cleaner: limpieza y validación
       3. data_analyzer: análisis estadístico" \
  --session-id data_pipeline_v1

# Paso 2: Usar los agentes
python coreee/sistema_agentes_supervisor_coder.py \
  -q "Ingesta datos de la API, limpia outliers y analiza distribuciones" \
  --session-id data_pipeline_v1 \
  --resume

# Paso 3: Ver qué agentes trabajaron
python coreee/sistema_agentes_supervisor_coder.py \
  --agents-list --session-id data_pipeline_v1

# Paso 4: Siguiente iteración (nueva sesión)
python coreee/sistema_agentes_supervisor_coder.py \
  -q "Mejora el pipeline con validación schema" \
  --session-id data_pipeline_v2
```

---

## 🎉 Beneficios del Nuevo Sistema

✅ **Aislamiento completo** - Proyectos no interfieren entre sí  
✅ **Organización clara** - Cada sesión = un equipo  
✅ **Escalabilidad** - Puedes tener cientos de sesiones  
✅ **Experimentación segura** - Prueba agentes sin afectar otros proyectos  
✅ **Versionado** - data_pipeline_v1, data_pipeline_v2, etc.  
✅ **Colaboración** - Equipos diferentes en sesiones diferentes  

---

## 🔗 Referencias

- **Documentación de agentes**: `AGENTES_DINAMICOS.md`
- **Código fuente**: `coreee/agent_registry.py`
- **Sistema principal**: `coreee/sistema_agentes_supervisor_coder.py`

---

**¿Preguntas?** Revisa la documentación o abre un issue en el repositorio.
