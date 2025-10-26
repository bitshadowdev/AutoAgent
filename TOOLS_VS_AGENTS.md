# 🔧 Tools vs 🤖 Agents - Guía de Referencia Rápida

## Regla de Oro

**¿Necesitas EJECUTAR código?** → `create_tool`  
**¿Necesitas un EXPERTO que analice/opine?** → `create_agent`

---

## 🔧 TOOLS (create_tool)

### ¿Qué son?
Funciones Python ejecutables que realizan operaciones computacionales.

### Características:
- ✅ Código Python válido con `def nombre(args): ...`
- ✅ Pueden importar librerías
- ✅ Pueden acceder a archivos, red, APIs
- ✅ Devuelven resultados computados

### Cuándo usar:
- Scraping web
- Lectura/escritura de archivos
- Cálculos matemáticos
- Llamadas a APIs externas
- Procesamiento de datos (parsing, transformación)
- Operaciones del sistema

### Ejemplos:

#### ✅ Correcto: Tool para scraping
```json
{
  "type": "create_tool",
  "message": "Creando scraper de noticias",
  "tool": {
    "name": "scrape_news",
    "code": "import requests\nfrom bs4 import BeautifulSoup\n\ndef scrape_news(args):\n    url = args['url']\n    response = requests.get(url)\n    soup = BeautifulSoup(response.text, 'html.parser')\n    headlines = [h.text for h in soup.find_all('h2')[:10]]\n    return {'ok': True, 'headlines': headlines}"
  },
  "call": {
    "name": "scrape_news",
    "args": {"url": "https://example.com/news"}
  }
}
```

#### ✅ Correcto: Tool para cálculos
```json
{
  "type": "create_tool",
  "message": "Calculadora financiera",
  "tool": {
    "name": "calculate_roi",
    "code": "def calculate_roi(args):\n    investment = args['investment']\n    returns = args['returns']\n    roi = ((returns - investment) / investment) * 100\n    return {'roi': roi, 'profit': returns - investment}"
  },
  "call": {
    "name": "calculate_roi",
    "args": {"investment": 10000, "returns": 15000}
  }
}
```

---

## 🤖 AGENTS (create_agent)

### ¿Qué son?
Asistentes especializados con prompts personalizados que razonan sobre información.

### Características:
- ✅ NO requieren código Python
- ✅ Tienen un `system_prompt` que define su expertise
- ✅ Analizan, revisan, opinan, generan contenido
- ✅ Reciben contexto de la conversación

### Cuándo usar:
- Análisis y generación de insights
- Revisión de calidad/factualidad
- Diseño y estrategia
- Crítica constructiva
- Generación de contenido creativo
- Toma de decisiones basada en criterios

### Ejemplos:

#### ✅ Correcto: Agente verificador de hechos
```json
{
  "type": "create_agent",
  "message": "Necesito un verificador de hechos",
  "agent": {
    "name": "fact_checker",
    "role": "Verificador de Hechos Experto",
    "system_prompt": "Eres un verificador de hechos profesional. Tu trabajo es analizar afirmaciones y determinar su veracidad basándote en conocimiento general y lógica. Para cada afirmación, evalúas: 1) Si es verificable, 2) Si es verdadera/falsa/parcialmente verdadera, 3) Fuentes o razonamiento que lo respalda. Siempre eres escéptico pero justo.",
    "capabilities": ["verificación de hechos", "análisis crítico", "evaluación de fuentes"]
  },
  "call": {
    "agent_name": "fact_checker",
    "task": "Verifica si esta información es correcta: 'Python fue creado en 1991 por Guido van Rossum'"
  }
}
```

#### ✅ Correcto: Agente analista de datos
```json
{
  "type": "create_agent",
  "message": "Creando analista para interpretar resultados",
  "agent": {
    "name": "data_analyst",
    "role": "Analista de Datos Senior",
    "system_prompt": "Eres un analista de datos experto. Interpretas datasets, identificas patrones, detectas anomalías y generas insights accionables. Siempre proporcionas análisis cuantitativo Y cualitativo. Destacas tendencias, correlaciones y recomendaciones basadas en datos.",
    "capabilities": ["análisis estadístico", "identificación de patrones", "insights de negocio"]
  },
  "call": {
    "agent_name": "data_analyst",
    "task": "Analiza estas ventas mensuales: [100, 150, 120, 180, 200, 190] y genera insights"
  }
}
```

#### ✅ Correcto: Agente revisor de código
```json
{
  "type": "create_agent",
  "message": "Necesito un experto en code review",
  "agent": {
    "name": "code_reviewer",
    "role": "Revisor de Código Senior",
    "system_prompt": "Eres un revisor de código experimentado. Evalúas código en términos de: legibilidad, eficiencia, seguridad, mejores prácticas y mantenibilidad. Proporcionas críticas constructivas con ejemplos concretos de mejora. Priorizas problemas críticos sobre estilo.",
    "capabilities": ["revisión de código", "detección de bugs", "optimización", "seguridad"]
  },
  "call": {
    "agent_name": "code_reviewer",
    "task": "Revisa esta función y sugiere mejoras: def calc(x,y): return x+y"
  }
}
```

---

## ❌ Errores Comunes

### Error 1: Intentar crear un agente como tool

**❌ INCORRECTO:**
```json
{
  "type": "create_tool",
  "tool": {
    "name": "fact_checker_agent",
    "code": "un agente que verifica hechos..."  // NO es código Python válido
  }
}
```

**✅ CORRECTO:**
```json
{
  "type": "create_agent",
  "agent": {
    "name": "fact_checker",
    "system_prompt": "Eres un verificador de hechos..."
  }
}
```

### Error 2: Intentar hacer ejecución computacional con agente

**❌ INCORRECTO:**
```json
{
  "type": "create_agent",
  "agent": {
    "name": "file_reader",
    "system_prompt": "Lee archivos CSV..."  // Los agentes NO leen archivos
  }
}
```

**✅ CORRECTO:**
```json
{
  "type": "create_tool",
  "tool": {
    "name": "read_csv",
    "code": "import pandas as pd\ndef read_csv(args): return pd.read_csv(args['file']).to_dict()"
  }
}
```

---

## 🎯 Casos de Uso por Tarea

| Tarea | Tipo | Razón |
|-------|------|-------|
| "Obtén las últimas noticias de BBC" | `create_tool` | Requiere scraping/HTTP |
| "Analiza estas noticias y genera insights" | `create_agent` | Requiere análisis/razonamiento |
| "Lee el archivo ventas.csv" | `create_tool` | Requiere operación de archivo |
| "Interpreta los datos de ventas" | `create_agent` | Requiere interpretación |
| "Calcula el promedio de una lista" | `create_tool` | Requiere cálculo |
| "Sugiere estrategias basadas en estos números" | `create_agent` | Requiere estrategia |
| "Descarga imagen de esta URL" | `create_tool` | Requiere operación de red |
| "Diseña un logo conceptualmente" | `create_agent` | Requiere creatividad |
| "Ejecuta este query SQL" | `create_tool` | Requiere ejecución |
| "Revisa este query por seguridad" | `create_agent` | Requiere revisión |

---

## 🔄 Flujo de Decisión

```
¿Qué necesitas hacer?
│
├─ Ejecutar código / Operación computacional
│  └─> create_tool
│      └─> Debe tener: def nombre(args): ...
│
└─ Analizar / Opinar / Revisar / Generar contenido
   └─> create_agent
       └─> Debe tener: system_prompt con expertise
```

---

## 💡 Tips Finales

1. **Si dudas**: pregúntate "¿esto requiere ejecutar código Python?" → Sí = Tool, No = Agent

2. **Los agentes NO pueden**:
   - Leer archivos del sistema
   - Hacer peticiones HTTP
   - Ejecutar comandos
   - Calcular directamente

3. **Las tools NO pueden**:
   - "Pensar" o "analizar" sin computar
   - Dar opiniones subjetivas
   - Hacer crítica constructiva
   - Generar estrategias

4. **Combinación poderosa**: Tool lee datos → Agent analiza datos

5. **Nombres descriptivos**:
   - Tools: `scrape_news`, `calculate_roi`, `read_csv`
   - Agents: `fact_checker`, `data_analyst`, `code_reviewer`

---

## 🧪 Test de Comprensión

Para cada tarea, elige el tipo correcto:

1. "Verifica si este código tiene vulnerabilidades" → **Agent** ✓
2. "Ejecuta este código y devuelve resultado" → **Tool** ✓
3. "Genera ideas creativas para marketing" → **Agent** ✓
4. "Descarga el contenido de 10 URLs" → **Tool** ✓
5. "Analiza estos tweets y detecta sentiment" → **Agent** ✓
6. "Extrae texto de un PDF" → **Tool** ✓

---

**Recuerda**: Tools EJECUTAN, Agents RAZONAN. 🚀
