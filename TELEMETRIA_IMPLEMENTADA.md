# 📊 Sistema de Telemetría y Aprendizaje Implementado

## ✅ Funcionalidades Implementadas

### 1. **Motor de Diagnósticos Automáticos**
- **Ubicación**: `sistema_agentes_supervisor_coder.py` líneas 120-178
- **Reglas de Diagnóstico**:
  - `PY_NAMEERROR_IMPORT`: Detecta imports faltantes y sugiere el import correcto
  - `HTTP_404_VOICE_NOT_FOUND`: Detecta voice_id inválido en ElevenLabs
  - `CF_INVALID_PROMPT_NONE`: Detecta prompts vacíos enviados al LLM
  - `JSON_FORMAT_INVALID`: Detecta respuestas no-JSON del modelo
  - `PY_IMPORTERROR`: Detecta módulos no instalados

**Función**: `diagnose(text: str) -> Optional[Dict[str, Any]]`

### 2. **Telemetría de Herramientas**
- **Ubicación**: `sistema_agentes_supervisor_coder.py` líneas 645-677
- **Métricas Capturadas**:
  - ✅ Número de llamadas (totales, exitosas, fallidas)
  - ⏱️ Latencia promedio (suavizada exponencialmente)
  - 🔍 Último error con código
  - 📝 Sample de últimos argumentos usados
  - 📊 Score dinámico basado en:
    - Tasa de éxito (peso 1.0)
    - Tasa de error (penalización 0.6)
    - Latencia (penalización hasta 0.4)
    - Bonus por contribuir al éxito final (+0.2)

**Función**: `_update_tool_stats(tool_name, ok, latency_ms, args, result, contributed=False)`

### 3. **Preferencias del Usuario**
- **Ubicación**: `sistema_agentes_supervisor_coder.py` líneas 679-684
- **Captura Automática**:
  - `tts_preferred_voice_id`: Voice ID más exitoso en herramientas TTS
  - Extensible para otros patrones

**Función**: `_update_user_prefs(tool_name, args, ok)`

### 4. **Contexto Inteligente para el Coder**
- **Ubicación**: `sistema_agentes_supervisor_coder.py` líneas 686-706
- **Inyección Automática**:
  - Top 5 herramientas por score
  - Preferencias del usuario
  - Se inyecta antes de cada llamada al Coder (línea 756-757)

**Función**: `_inject_prefs_for_coder(transcript)`

### 5. **Persistencia de Telemetría**
- **Ubicación**: `sistema_agentes_supervisor_coder.py` líneas 632-643
- **Datos Persistidos**:
  - `tool_stats`: Todas las métricas de herramientas
  - `agent_stats`: Métricas de agentes (preparado)
  - `user_prefs`: Preferencias capturadas
  - `agents_used`: Lista de agentes utilizados

**Función**: `_save_session_snapshot(transcript, task, turn, status)`

### 6. **Bonus por Éxito Final**
- **Ubicación**: `sistema_agentes_supervisor_coder.py` líneas 1060-1063
- **Lógica**: Cuando el Supervisor decide `route='end'`, la última herramienta usada recibe +0.2 en su score

### 7. **Cliente LLM Robusto**
- **Ubicación**: `llm_client.py`
- **Mejoras**:
  - ✅ Sesión HTTP con reintentos automáticos (3 intentos)
  - ⏱️ Timeouts configurados (5s conexión, 60s lectura)
  - 🛡️ Validación de prompt (no vacío/nulo)
  - 📊 Respuestas vacías retornan error estructurado

### 8. **Post-procesamiento Automático**
- **Ubicación**: `sistema_agentes_supervisor_coder.py` línea 181-185, 843-845
- **Función**: `_postprocess_result_html(result)`
- **Funcionalidad**: Convierte `audio_base64` en tag HTML `<audio>` con autoplay

### 9. **Visualización en CLI**
- **Ubicación**: `manage_sessions.py` líneas 101-129
- **Comando**: `python manage_sessions.py show <session_id>`
- **Muestra**:
  - 📊 Top 5 tools por score
  - Métricas detalladas (calls, ok/errors, latencia, último error)
  - ⭐ Preferencias del usuario

### 10. **Errores Estructurados en ToolRegistry**
- **Ubicación**: `sistema_agentes_supervisor_coder.py` líneas 320-390
- **Campos Agregados**:
  - `code`: Código de error (ej: `PY_NAMEERROR_IMPORT`)
  - `blame`: Responsable (`tool_code`, `env`, `input`, `network`)
  - `suggestion`: Mensaje accionable
  - `traceback`: Stack trace limitado

## 🔄 Flujo de Telemetría

```
1. User Task → Sistema
2. Coder recibe contexto con top_tools y user_prefs
3. Tool se ejecuta:
   ├─ Se mide latencia (perf_counter)
   ├─ Se captura resultado
   ├─ Post-procesamiento (audio → HTML)
   ├─ Diagnóstico automático si hay error
   └─ Actualización de stats + prefs
4. Timeline registra evento "tool_scored"
5. Supervisor decide:
   ├─ route='end' → Bonus a última tool
   └─ route='coder' → Continuar
6. Snapshot de sesión persiste telemetría
```

## 📈 Ejemplo de Datos Persistidos

```json
{
  "tool_stats": {
    "generate_and_play_poem": {
      "calls": 3,
      "ok": 3,
      "errors": 0,
      "avg_latency_ms": 1250.5,
      "last_error": null,
      "last_args_sample": {"api_key": "sk_***", "text": "Poema..."},
      "score": 0.95,
      "last_ok_at": "2025-10-26T02:30:00Z"
    },
    "scrape_books_to_html": {
      "calls": 2,
      "ok": 1,
      "errors": 1,
      "avg_latency_ms": 3200.0,
      "last_error": "PY_NAMEERROR_IMPORT: requests",
      "score": 0.12,
      "last_ok_at": "2025-10-26T02:25:00Z"
    }
  },
  "user_prefs": {
    "tts_preferred_voice_id": "EXAVITQu4vr4xnSDxMaL"
  },
  "agents_used": []
}
```

## 🚀 Cómo Usar

### Ver Telemetría de una Sesión
```bash
python coreee/manage_sessions.py show 20251025_232548
```

### Reanudar Sesión con Contexto Aprendido
```bash
python coreee/sistema_agentes_supervisor_coder.py --session-id 20251025_232548 --resume
```

El sistema automáticamente:
- Restaura las métricas previas
- Inyecta el ranking de tools al Coder
- Usa las preferencias del usuario
- Prefiere herramientas con mejor score

## 🎯 Beneficios

1. **Aprendizaje Continuo**: El sistema recuerda qué funcionó y prefiere esas herramientas
2. **Diagnóstico Rápido**: Errores comunes se detectan y sugieren soluciones automáticamente
3. **UX Mejorada**: Audio se convierte automáticamente en HTML reproducible
4. **Decisiones Informadas**: El Coder ve métricas reales antes de elegir herramientas
5. **Debugging Facilitado**: CLI muestra claramente qué tools funcionaron mejor
6. **Persistencia Total**: Todo se guarda en sesiones, visible incluso después de cerrar

## 🔮 Próximas Mejoras Sugeridas (Opcionales)

1. **UCB1 para Exploración**: Balance entre explotar herramientas conocidas y explorar nuevas
2. **Auto-remediación con Playbooks**: Sistema intenta fix automático (ej: listar voces y reintentar TTS)
3. **Métricas de Agentes**: Mismo sistema para agentes dinámicos
4. **Scrubbing de Secretos en Timeline**: Enmascarar API keys en eventos
5. **Auto-test de Tools**: Ejecutar selftest antes de registrar herramienta nueva
