# 🔄 Sistema de Retry Automático con Corrección de Errores

## Mejoras Implementadas

### 1. ✅ Detección y Reporte Mejorado de Errores

#### Antes:
```json
{"error": "name 'requests' is not defined"}
```

#### Ahora:
```json
{
  "ok": false,
  "error": "NameError: name 'requests' is not defined",
  "suggestion": "Probablemente falta un 'import' al inicio del código. Agrégalo y vuelve a intentar.",
  "traceback": "..."
}
```

**Tipos de errores detectados específicamente:**
- `NameError` → Falta import
- `ImportError` → Módulo no instalado
- `KeyError` → Falta clave en diccionario
- `Exception` → Error genérico con traceback completo

### 2. ✅ Actualización de Herramientas con Errores

#### Antes:
- Si una herramienta fallaba, el sistema NO podía sobrescribirla
- El Coder creaba herramientas con nombres diferentes
- El error se repetía indefinidamente

#### Ahora:
- **Las herramientas se pueden actualizar** usando el mismo nombre
- El sistema detecta si es creación nueva o actualización
- Se muestra mensaje: `[⟳ HERRAMIENTA ACTUALIZADA] nombre ha sido corregida/mejorada`

**Ejemplo de flujo:**
```
Turno 1: Crea herramienta fetch_news() → ❌ Error: falta import requests
Turno 2: Actualiza fetch_news() → ✅ Agrega import, funciona correctamente
```

### 3. ✅ Prompts Mejorados

#### Prompt del Coder - Nuevas instrucciones:
```
**IMPORTANTE: SIEMPRE incluye TODOS los imports necesarios al inicio del código**.
- Si usas `requests`, `json`, `re`, etc., debes importarlos explícitamente.

**CORRECCIÓN DE ERRORES**:
- Si una herramienta falló, DEBES corregirla creando una nueva versión con el MISMO nombre.
- Lee cuidadosamente el error reportado y corrígelo específicamente.
- Si falta un import, agrégalo. Si hay un bug lógico, corrígelo.
- NO ignores los errores previos, apréndelos y corrígelos.
```

#### Prompt del Supervisor - Mejoras:
```
- **Si hay un ERROR de ejecución -> coder con tips específicos de corrección**.
- **CRÍTICO para errores**: Si ves un error como "name 'X' is not defined", 
  el primer tip debe ser "Agrega 'import X' al inicio del código".
- **Prioriza la corrección de errores sobre nuevas features**.
```

### 4. ✅ Feedback Enriquecido con Tips Accionables

#### Antes:
```
[Supervisor] Continúa, falta completar o mejorar la respuesta.
```

#### Ahora:
```
[Supervisor] No se pudieron obtener las noticias porque la función falló.

Acciones requeridas:
  1. Agrega 'import requests' al inicio del código
  2. Implementa manejo de errores con try/except
  3. Verifica que la respuesta JSON contiene la clave esperada
  4. Parsea la respuesta y extrae título, enlace y descripción
  5. Devuelve una lista formateada de noticias
  
🔄 Por favor, corrige los errores y vuelve a intentar.
```

### 5. ✅ Más Turnos por Defecto

#### Antes:
```
max_turns = 5
```

#### Ahora:
```
max_turns = 10  # Permite más iteraciones para corregir errores
```

Configurable con: `--max-turns N`

### 6. ✅ Visualización de Errores en Transcript

Cuando una herramienta falla, el transcript ahora muestra:

```
[Coder] Creando herramienta para obtener noticias

Herramienta usada: fetch_news
Args: {"api_key": "...", "query": "AI"}
Resultado: {"ok": false, "error": "NameError: name 'requests' is not defined"}

⚠️ ERROR EN HERRAMIENTA: NameError: name 'requests' is not defined
💡 Sugerencia: Probablemente falta un 'import' al inicio del código. Agrégalo y vuelve a intentar.
Traceback: ...
```

---

## 🧪 Cómo Probar las Mejoras

### Prueba 1: Error de Import Faltante

```bash
cd coreee
python sistema_agentes_supervisor_coder.py -q "Obtén las últimas noticias de IA usando requests" --session-id test_import
```

**Comportamiento esperado:**
1. Turno 1: Crea herramienta sin `import requests` → ❌ Error
2. Supervisor detecta error y sugiere agregar import
3. Turno 2: Actualiza herramienta con `import requests` → ✅ Funciona

### Prueba 2: Error de API/Lógica

```bash
python sistema_agentes_supervisor_coder.py -q "Calcula el factorial de 5 y guárdalo en un archivo" --session-id test_logic
```

**Comportamiento esperado:**
1. Si falta manejo de errores, el Supervisor lo detecta
2. Se sugiere agregar try/except
3. Se actualiza la herramienta con mejor manejo de errores

### Prueba 3: Verificar Actualización de Herramientas

```bash
# Primera ejecución
python sistema_agentes_supervisor_coder.py -q "Crea una función 'sumar' que sume dos números" --session-id test_update

# Segunda ejecución - mejorar la misma función
python sistema_agentes_supervisor_coder.py -q "Mejora la función 'sumar' para validar que los inputs sean números" --session-id test_update --resume
```

**Comportamiento esperado:**
- La función `sumar` se actualiza en lugar de crear `sumar_v2`
- Se muestra: `[⟳ HERRAMIENTA ACTUALIZADA] sumar ha sido corregida/mejorada`

### Prueba 4: Ver Sesión con Errores Corregidos

```bash
# Después de una ejecución con errores
python manage_sessions.py show test_import
```

Verás el historial completo de cómo se corrigió el error.

---

## 📊 Ejemplo Completo de Flujo

### Comando:
```bash
python sistema_agentes_supervisor_coder.py -q "Dame las últimas noticias de tecnología usando SerpAPI con esta key: abc123" --session-id news_test -m 15
```

### Flujo Esperado:

**Turno 1:**
```
[Coder] Creando herramienta fetch_tech_news
```
→ ❌ Error: `name 'requests' is not defined`

**Turno 2:**
```
[Supervisor] La herramienta falló por falta de import.

Acciones requeridas:
  1. Agrega 'import requests' al inicio del código
  2. Implementa try/except para errores de red
  3. Valida la respuesta de la API
```

**Turno 3:**
```
[Coder] Actualizando fetch_tech_news con imports necesarios
[⟳ HERRAMIENTA ACTUALIZADA] fetch_tech_news ha sido corregida
```
→ ✅ Funciona correctamente

**Turno 4:**
```
[Supervisor] route: end
Respuesta final con noticias obtenidas exitosamente
```

---

## 🎯 Ventajas del Sistema Mejorado

### 1. Auto-corrección Iterativa
- El sistema aprende de sus errores
- No se repiten los mismos errores indefinidamente
- Las herramientas se mejoran progresivamente

### 2. Feedback Más Claro
- Errores específicos con sugerencias
- Tips accionables del Supervisor
- Traceback limitado para mejor legibilidad

### 3. Persistencia Inteligente
- Las correcciones se guardan permanentemente
- Versiones mejoradas reemplazan las defectuosas
- Historial completo en sesiones

### 4. Mayor Tasa de Éxito
- Con 10 turnos en lugar de 5
- Detección específica de tipos de error
- Guía paso a paso para correcciones

---

## 🔧 Configuración Avanzada

### Ajustar Número de Turnos

```bash
# Más turnos para tareas complejas
python sistema_agentes_supervisor_coder.py -q "tarea compleja" -m 20

# Menos turnos para tareas simples
python sistema_agentes_supervisor_coder.py -q "tarea simple" -m 5
```

### Ver Timeline de Correcciones

Después de ejecutar, revisa:
```
.runs/FECHA_HORA/timeline.md
```

Verás eventos como:
- `tool_create` - Creación inicial
- `tool_update` - Actualización/corrección
- `tool_result_error` - Error detectado
- `tool_result_ok` - Ejecución exitosa

### Exportar Sesión con Correcciones

```bash
# Exportar sesión exitosa para reutilizar
python manage_sessions.py export news_test --output backup_news.json

# Importar en otro sistema
python manage_sessions.py import backup_news.json
```

---

## 📝 Notas Importantes

1. **Imports Automáticos**: El sistema sugiere agregar imports pero NO los instala automáticamente. Para instalar paquetes, el Coder debe crear código que use `subprocess.run(['pip', 'install', 'paquete'])`.

2. **Límite de Correcciones**: Con `max_turns=10`, el sistema tiene hasta 10 intentos. Si un error persiste después de múltiples correcciones, revisa manualmente el código generado en `.permanent_tools/`.

3. **Persistencia de Errores**: Si una herramienta con error se guardó, será reemplazada automáticamente cuando se corrija.

4. **Logs Detallados**: Todos los eventos (creación, actualización, errores) se registran en `.runs/` para análisis posterior.

---

## 🚀 Resultado Final

Con estas mejoras, el sistema ahora:

✅ **Detecta** errores específicos (imports, lógica, API)  
✅ **Informa** al Coder con sugerencias accionables  
✅ **Corrige** actualizando herramientas con el mismo nombre  
✅ **Persiste** las correcciones para uso futuro  
✅ **Itera** hasta resolver el problema o agotar turnos  

El ciclo de **error → detección → corrección → éxito** es ahora completamente automático. 🎉
