# 🤖 Sistema de Agentes Dinámicos

El sistema AutoAgent ahora puede **crear agentes especializados** durante la ejecución. Los agentes Coder y Supervisor actúan como "meta-agentes" que pueden crear nuevos agentes para tareas específicas.

## 🎯 Concepto

### Agentes Primordiales (Fijos)
- **Coder**: Programador que crea herramientas y agentes
- **Supervisor**: Evalúa resultados y dirige el flujo

### Agentes Dinámicos (Creados en Runtime)
- **Data Analyst**: Especializado en análisis de datos
- **UX Designer**: Experto en diseño de interfaces
- **Security Auditor**: Especialista en seguridad
- **Content Writer**: Creador de contenido
- *(Y cualquier otro que el Coder decida crear)*

## 🔧 Cómo Funciona

### 1. El Coder Decide Crear un Agente

Cuando el Coder detecta que necesita ayuda especializada:

```json
{
  "type": "create_agent",
  "message": "Necesitamos un analista de datos para procesar este CSV",
  "agent": {
    "name": "data_analyst",
    "role": "Analista de Datos Experto",
    "system_prompt": "Eres un experto en análisis de datos. Tu especialidad es procesar datasets, extraer insights estadísticos, identificar patrones y generar visualizaciones. Siempre proporciona análisis cuantitativos y cualitativos.",
    "capabilities": ["análisis estadístico", "visualización", "limpieza de datos", "insights"]
  },
  "call": {
    "agent_name": "data_analyst",
    "task": "Analiza el archivo ventas.csv y genera un reporte con tendencias"
  }
}
```

### 2. El Agente se Crea y Ejecuta

El sistema:
1. Crea el agente con su prompt personalizado
2. Lo registra en memoria
3. Lo persiste a disco (`.agents/`)
4. Lo llama inmediatamente con la tarea
5. El agente responde con su perspectiva especializada

### 3. Reutilización del Agente

En turnos posteriores o sesiones futuras:

```json
{
  "type": "call_agent",
  "message": "Consultemos al analista de datos sobre estos nuevos números",
  "call": {
    "agent_name": "data_analyst",
    "task": "Compara estos resultados con el análisis anterior"
  }
}
```

## 📁 Estructura de Persistencia

```
.agents/
├── manifest.json              # Índice de todos los agentes
├── data_analyst.json          # Definición del analista de datos
├── ux_designer.json           # Definición del diseñador UX
└── security_auditor.json      # Definición del auditor de seguridad
```

### Ejemplo de Definición (data_analyst.json):

```json
{
  "name": "data_analyst",
  "role": "Analista de Datos Experto",
  "system_prompt": "Eres un experto en análisis de datos...",
  "capabilities": ["análisis estadístico", "visualización", "limpieza de datos"],
  "created_at": "2025-10-25T22:30:00Z",
  "created_by": "coder",
  "temperature": 0.7,
  "max_tokens": 1500,
  "model": "@cf/openai/gpt-oss-120b"
}
```

## 🎨 Casos de Uso

### Caso 1: Análisis de Datos Complejo

```bash
python sistema_agentes_supervisor_coder.py -q "Analiza el dataset ventas_2024.csv y genera insights de negocio" --session-id analisis_ventas
```

**Flujo:**
1. Coder analiza la tarea
2. Decide crear un `data_analyst`
3. El analista procesa el CSV
4. Genera insights estadísticos
5. El Coder presenta los resultados

### Caso 2: Revisión de Seguridad

```bash
python sistema_agentes_supervisor_coder.py -q "Revisa mi código auth.py y encuentra vulnerabilidades" --session-id security_review
```

**Flujo:**
1. Coder detecta necesidad de expertise en seguridad
2. Crea `security_auditor`
3. El auditor revisa el código
4. Identifica vulnerabilidades
5. Propone correcciones

### Caso 3: Diseño de UI/UX

```bash
python sistema_agentes_supervisor_coder.py -q "Diseña una interfaz para dashboard de analytics" --session-id dashboard_design
```

**Flujo:**
1. Coder reconoce tarea de diseño
2. Crea `ux_designer`
3. El diseñador propone estructura
4. Sugiere componentes y paleta de colores
5. Genera código HTML/CSS

### Caso 4: Múltiples Agentes Colaborando

```bash
python sistema_agentes_supervisor_coder.py -q "Crea una app de finanzas: diseño + análisis de datos + seguridad" --session-id finanzas_app -m 20
```

**Flujo:**
1. Coder crea `ux_designer` para UI
2. Crea `data_analyst` para métricas financieras
3. Crea `security_auditor` para validación
4. Los agentes colaboran en sus áreas
5. El Coder integra todo

## 📊 Comandos CLI

### Listar Agentes Creados

```bash
python sistema_agentes_supervisor_coder.py --agents-list
```

**Salida:**
```
Agentes dinámicos en C:\...\AutoAgent\.agents:

Nombre               Rol                            Capacidades                              Creado por     
==============================================================================================================
data_analyst         Analista de Datos Experto      análisis, visualización, insights        coder          
ux_designer          Diseñador UX/UI                diseño, wireframes, accesibilidad        coder          
security_auditor     Auditor de Seguridad           pentesting, análisis de código...        coder          

Total: 3 agentes
```

### Cambiar Directorio de Agentes

```bash
python sistema_agentes_supervisor_coder.py --agents-dir /ruta/custom -q "tarea"
```

### Ver Agentes Usados en una Sesión

```bash
python manage_sessions.py show mi_sesion
```

Muestra:
- Tools usadas
- **Agentes creados/usados**
- Transcript completo

## 🔄 Actualización de Agentes

Los agentes se pueden actualizar igual que las herramientas:

```json
{
  "type": "create_agent",
  "message": "Mejorando al analista con capacidad de ML",
  "agent": {
    "name": "data_analyst",  // Mismo nombre = actualización
    "role": "Analista de Datos + ML",
    "system_prompt": "Eres un experto en análisis de datos Y machine learning...",
    "capabilities": ["análisis", "visualización", "machine learning", "predicciones"]
  }
}
```

**Resultado:**
```
[⟳ AGENTE ACTUALIZADO] data_analyst (Analista de Datos + ML)
```

## 💡 Buenas Prácticas

### 1. Nombres Descriptivos
```
✅ data_analyst, security_auditor, ux_designer
❌ agent1, helper, temp
```

### 2. Prompts Específicos
```
✅ "Eres un experto en análisis de datos financieros. Priorizas ROI, métricas de conversión y análisis de tendencias."
❌ "Eres un agente que hace cosas."
```

### 3. Capacidades Claras
```
✅ ["análisis estadístico", "detección de outliers", "generación de reportes"]
❌ ["todo", "general", "varios"]
```

### 4. Crear Solo Cuando sea Necesario
No crear agentes para tareas simples que el Coder puede hacer directamente.

### 5. Reutilizar Agentes Existentes
Antes de crear uno nuevo, verificar si ya existe uno similar.

## 🧪 Ejemplo Completo

### Comando:
```bash
python sistema_agentes_supervisor_coder.py -q "Analiza el rendimiento de mi sitio web y sugiere mejoras" --session-id web_optimization -m 15
```

### Transcript Esperado:

```
[ASSISTANT] [Coder] Voy a crear un agente especializado en performance web

Agente creado: web_performance_expert
Rol: Experto en Optimización Web
Capacidades: análisis de performance, optimización de assets, SEO técnico

[✨ AGENTE CREADO] web_performance_expert (Experto en Optimización Web)

[ASSISTANT] [Agente: web_performance_expert] (Experto en Optimización Web)

Tarea: Analiza el sitio web y genera reporte de optimización

Respuesta:
He analizado el sitio y encontré las siguientes oportunidades:

1. **Imágenes**: 
   - 45% de las imágenes sin optimizar
   - Recomiendo WebP con compresión 85%
   - Ahorro potencial: 2.3MB

2. **JavaScript**:
   - Bundle principal: 850KB (muy grande)
   - Sugerencia: code splitting + lazy loading
   - Reducción esperada: 60%

3. **Caching**:
   - Headers de caché faltantes
   - Implementar Cache-Control y ETags

4. **Core Web Vitals**:
   - LCP: 3.2s → objetivo <2.5s
   - FID: 85ms → ✅ bueno
   - CLS: 0.18 → reducir a <0.1

[Supervisor] route: coder
Acciones requeridas:
  1. Crea herramientas para implementar las optimizaciones sugeridas
  2. Verifica que las métricas mejoren
  3. Genera reporte final

[ASSISTANT] [Coder] Creando herramienta para optimizar imágenes...
```

## 🔒 Seguridad

### Consideraciones

1. **Los agentes tienen el mismo nivel de acceso que el Coder** (modo abierto)
2. **Pueden ejecutar código arbitrario** en sus respuestas
3. **Persisten en disco** y se cargan automáticamente

### Recomendaciones

- Revisar agentes creados con `--agents-list`
- No permitir creación de agentes en producción sin revisión
- Los prompts de agentes deben incluir restricciones de seguridad
- Usar en entornos controlados

## 📈 Ventajas del Sistema

### 1. Especialización
Cada agente tiene un dominio de expertise claro.

### 2. Modularidad
Los agentes son independientes y reutilizables.

### 3. Escalabilidad
Se pueden crear tantos agentes como se necesiten.

### 4. Persistencia
Los agentes sobreviven entre sesiones.

### 5. Colaboración
Múltiples agentes pueden trabajar en la misma tarea.

### 6. Flexibilidad
El Coder decide dinámicamente qué agentes crear.

## 🎓 Conceptos Avanzados

### Cadena de Agentes

Un agente puede sugerir la creación de otro agente:

```
Coder → crea data_analyst
data_analyst → sugiere crear data_visualizer
Coder → crea data_visualizer
data_visualizer → genera gráficos
```

### Agentes con Memoria

Los agentes reciben contexto de los últimos 5 mensajes, permitiendo:
- Referencias a información previa
- Continuidad en la conversación
- Decisiones basadas en historial

### Agentes Especializados por Dominio

```python
# Finanzas
financial_analyst = {
    "name": "financial_analyst",
    "system_prompt": "Experto en análisis financiero, ratios, valoración..."
}

# Legal
legal_advisor = {
    "name": "legal_advisor",
    "system_prompt": "Abogado especializado en cumplimiento normativo..."
}

# Marketing
marketing_strategist = {
    "name": "marketing_strategist",
    "system_prompt": "Estratega de marketing con expertise en SEO, SEM, contenido..."
}
```

## 🚀 Roadmap Futuro

Posibles mejoras:

- [ ] Agentes con herramientas propias
- [ ] Comunicación directa entre agentes
- [ ] Jerarquías de agentes (agente líder + sub-agentes)
- [ ] Agentes con acceso a APIs externas
- [ ] Templates de agentes pre-definidos
- [ ] Votación/consenso entre múltiples agentes
- [ ] Agentes reactivos (triggers automáticos)

## 📝 Resumen

El sistema de agentes dinámicos transforma AutoAgent de un sistema de 2 agentes fijos (Coder + Supervisor) a un **ecosistema extensible** donde:

✅ Se crean agentes especializados según la necesidad  
✅ Los agentes persisten y se reutilizan  
✅ Múltiples agentes colaboran en tareas complejas  
✅ El sistema se auto-organiza y escala  

**Resultado:** Un sistema verdaderamente multi-agente, adaptable y poderoso. 🎉
