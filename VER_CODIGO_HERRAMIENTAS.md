# 🔧 Ver Código de Herramientas en el Dashboard

## ✅ Funcionalidad Implementada

El dashboard ahora muestra el **código completo** de todas las herramientas creadas por el sistema.

---

## 🎯 Cómo Ver el Código

### Paso 1: Abre el Dashboard

```bash
streamlit run dashboard_streamlit.py
```

### Paso 2: Ve al Tab "🔧 Herramientas"

Encontrarás 5 tabs en el dashboard:
1. 📋 Timeline
2. 💬 Conversación
3. **🔧 Herramientas** ← Este
4. 📊 Estadísticas
5. 🔍 Inspector

### Paso 3: Expande la Herramienta

Verás algo como:

```
▼ 🔧 scrape_all_quotes (1 versión/es)
  
  Versión 1 - 13:47:28
  ─────────────────────────────────────────────
    1  def scrape_all_quotes(args):
    2      import requests
    3      from bs4 import BeautifulSoup
    4      import json
    5      
    6      base_url = "https://quotes.toscrape.com"
    7      all_quotes = []
    8      page = 1
    9      
   10      while True:
   11          url = f"{base_url}/page/{page}/"
   12          ...
  
  📊 450 caracteres
  ─────────────────────────────────────────────
```

---

## 🎨 Características

### 1. Código Completo con Syntax Highlighting

- ✅ Código Python con colores
- ✅ Números de línea
- ✅ Fácil de leer

### 2. Historial de Versiones

Si una herramienta fue **actualizada**, verás todas las versiones:

```
▼ 🔧 calculadora (3 versión/es)
  
  Versión 3 - 14:30:15
  [código más reciente]
  
  Versión 2 - 14:25:10
  [versión intermedia]
  
  Versión 1 - 14:20:05
  [versión inicial]
```

### 3. Información Adicional

- **Timestamp**: Cuándo se creó/actualizó
- **Tamaño**: Cantidad de caracteres
- **Versión**: Número de versión

### 4. Expanders Automáticos

Los expanders se abren automáticamente (`expanded=True`) para que veas el código de inmediato.

---

## 📊 Ejemplo Completo

### Después de ejecutar:

```bash
python coreee/sistema_agentes_supervisor_coder.py -q "Crea una calculadora y suma 10 + 5"
```

### En el Dashboard - Tab "Herramientas":

```
🔧 Herramientas Creadas/Actualizadas
─────────────────────────────────────────────

▼ 🔧 calculadora (1 versión/es)
  
  Versión 1 - 13:50:22
  ─────────────────────────────────────────────
    1  def calculadora(args):
    2      a = args.get('a', 0)
    3      b = args.get('b', 0)
    4      operation = args.get('operation', 'add')
    5      
    6      if operation == 'add':
    7          result = a + b
    8      elif operation == 'subtract':
    9          result = a - b
   10      elif operation == 'multiply':
   11          result = a * b
   12      elif operation == 'divide':
   13          if b != 0:
   14              result = a / b
   15          else:
   16              return {'ok': False, 'error': 'División por cero'}
   17      else:
   18          return {'ok': False, 'error': 'Operación desconocida'}
   19      
   20      return {'ok': True, 'result': result}
  
  📊 520 caracteres
  ─────────────────────────────────────────────
```

---

## 🔍 Fallback Inteligente

El sistema intenta obtener el código de dos fuentes:

1. **Primero**: Del evento directo (`data.code`)
2. **Si falla**: Del archivo guardado (`data.code_path`)

Esto asegura que **siempre** puedas ver el código, incluso en sesiones antiguas.

---

## 🎯 Casos de Uso

### 1. Ver Código Creado

Para ver qué herramienta creó el sistema:
1. Ve al Tab "Herramientas"
2. Expande la herramienta
3. Lee el código completo

### 2. Comparar Versiones

Si el sistema actualizó una herramienta:
1. Ve al Tab "Herramientas"
2. Expande la herramienta
3. Compara las diferentes versiones

### 3. Copiar Código

Para usar la herramienta tú mismo:
1. Ve al Tab "Herramientas"
2. Selecciona y copia el código
3. Úsalo en tu proyecto

---

## 🚨 Solución de Problemas

### No aparecen herramientas

**Causa**: No se han creado herramientas en esta sesión

**Solución**: 
- Ejecuta una tarea que requiera crear herramientas
- Ejemplo: `python coreee/sistema_agentes_supervisor_coder.py -q "Crea una herramienta que..."`

### Dice "Código no disponible"

**Causa 1**: El evento no tiene el código guardado

**Solución**: Esto solo pasa en sesiones muy antiguas. Ejecuta una nueva tarea.

**Causa 2**: El archivo de código fue eliminado

**Solución**: El código debería estar en `data.code` ahora, no debería fallar.

### Solo veo algunas herramientas

**Causa**: Filtros activos en el sidebar

**Solución**:
1. Sidebar → Filtros
2. Asegurar que todos los roles estén seleccionados
3. Especialmente "coder" (que crea las herramientas)

---

## 📋 Verificación Rápida

Después de ejecutar una tarea:

### ✅ Checklist

1. ✅ Dashboard abierto
2. ✅ Tab "🔧 Herramientas" seleccionado
3. ✅ Ver lista de herramientas creadas
4. ✅ Expander abierto automáticamente
5. ✅ Código visible con syntax highlighting
6. ✅ Números de línea
7. ✅ Información del tamaño

---

## 💡 Tips

### 1. Buscar Herramienta Específica

Las herramientas están agrupadas por nombre. Si creaste muchas:
- Busca visualmente el nombre
- O usa Ctrl+F en el navegador

### 2. Ver Solo Herramientas

En el sidebar:
1. Filtros → Desmarcar todos
2. Marcar solo "coder"
3. Ir al Tab "Timeline"
4. Ver todos los eventos `tool_create`

### 3. Copiar Código Fácilmente

El bloque de código tiene un botón de copiar en la esquina superior derecha (Streamlit lo agrega automáticamente).

---

## 🎨 Vista Previa

### Dashboard - Tab Herramientas

```
╔════════════════════════════════════════════════╗
║ 🔧 Herramientas Creadas/Actualizadas          ║
╠════════════════════════════════════════════════╣
║                                                ║
║ ▼ 🔧 scrape_all_quotes (1 versión/es)         ║
║   ┌──────────────────────────────────────┐    ║
║   │ Versión 1 - 13:47:28                 │    ║
║   │ ────────────────────────────────────│    ║
║   │   1  def scrape_all_quotes(args):    │    ║
║   │   2      import requests             │    ║
║   │   3      from bs4 import ...         │    ║
║   │   4      ...                         │    ║
║   │                                      │    ║
║   │ 📊 450 caracteres                    │    ║
║   └──────────────────────────────────────┘    ║
║                                                ║
║ ▼ 🔧 calculadora (2 versión/es)                ║
║   ┌──────────────────────────────────────┐    ║
║   │ Versión 2 - 14:10:30                 │    ║
║   │ [código actualizado]                 │    ║
║   │                                      │    ║
║   │ Versión 1 - 14:05:15                 │    ║
║   │ [código original]                    │    ║
║   └──────────────────────────────────────┘    ║
╚════════════════════════════════════════════════╝
```

---

## 🚀 Mejoras Implementadas

1. ✅ **Filtro mejorado**: Captura `tool_create` y `tool_update`
2. ✅ **Fallback inteligente**: Lee de `data.code` o `code_path`
3. ✅ **Expanders abiertos**: Código visible inmediatamente
4. ✅ **Información adicional**: Muestra tamaño del código
5. ✅ **Manejo de errores**: Si no hay código, muestra advertencia clara

---

## 🎉 Resultado

Ahora puedes ver **TODO el código** de las herramientas creadas:

- ✅ Código completo con syntax highlighting
- ✅ Números de línea
- ✅ Historial de versiones
- ✅ Información de tamaño
- ✅ Fácil de copiar
- ✅ Siempre disponible

---

**¡Abre el Tab "Herramientas" y verás todo el código!** 🔧✨
