import os
import json
from pathlib import Path

def generate_frontend_html(args: dict) -> dict:
    """Genera un archivo HTML que muestra los runs y sus eventos.
    Args:
        args: dict con claves:
            core_path (str): ruta absoluta a la carpeta que contiene los módulos Python (coreee).
            runs_path (str): ruta absoluta a la carpeta que contiene los archivos JSON de los runs (.runs).
            output_path (str, opcional): ruta completa del HTML a crear. Si no se indica, se crea en el directorio actual como 'frontend.html'.
    Returns:
        dict con 'ok': True y 'output_path' si se creó correctamente, o 'ok': False y 'error' en caso de falla.
    """
    try:
        core_path = Path(args.get('core_path'))
        runs_path = Path(args.get('runs_path'))
        output_path = Path(args.get('output_path', Path.cwd() / 'frontend.html'))
        # Validar rutas
        if not core_path.is_dir():
            return {"ok": False, "error": f"core_path '{core_path}' no es una carpeta válida"}
        if not runs_path.is_dir():
            return {"ok": False, "error": f"runs_path '{runs_path}' no es una carpeta válida"}
        # Leer módulos Python (solo para incluir como referencia en el html opcionalmente)
        core_modules = []
        for py_file in core_path.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
                core_modules.append({"path": str(py_file.relative_to(core_path)), "content": content})
            except Exception as e:
                # Ignorar ficheros que no se puedan leer
                continue
        # Leer runs JSON
        runs = []
        for json_file in runs_path.rglob('*.json'):
            try:
                data = json.loads(json_file.read_text(encoding='utf-8'))
                # Normalizamos el formato esperado: cada run debe tener al menos un id o nombre y lista de eventos
                run_id = data.get('id') or data.get('run_id') or data.get('name') or json_file.stem
                events = data.get('events') or []
                runs.append({
                    "id": str(run_id),
                    "name": str(data.get('name') or run_id or json_file.stem),
                    "events": events,
                    "source_file": str(json_file.relative_to(runs_path))
                })
            except Exception as e:
                # Si el archivo no es JSON válido, lo ignoramos
                continue
        # Generar HTML
        html_template = f"""
<!DOCTYPE html>
<html lang='es'>
<head>
    <meta charset='UTF-8'>
    <title>Frontend de Runs y Eventos</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        tr:hover {{ background-color: #f1f1f1; cursor: pointer; }}
        .event-list {{ margin-top: 20px; }}
        .event-item {{ border: 1px solid #ccc; padding: 8px; margin-bottom: 5px; background: #fafafa; }}
    </style>
</head>
<body>
    <h1>Runs Registrados</h1>
    <table id='runsTable'>
        <thead>
            <tr><th>ID</th><th>Nombre</th><th>Archivo origen</th></tr>
        </thead>
        <tbody></tbody>
    </table>
    <div class='event-list' id='eventList'>
        <h2>Eventos del Run seleccionado</h2>
        <div id='eventsContainer'>Selecciona un run para ver sus eventos.</div>
    </div>
    <script>
        const runs = {json.dumps(runs, ensure_ascii=False, indent=2)};
        const runsTableBody = document.querySelector('#runsTable tbody');
        const eventsContainer = document.getElementById('eventsContainer');
        function renderRuns() {{
            runs.forEach((run, idx) => {{
                const tr = document.createElement('tr');
                tr.dataset.index = idx;
                tr.innerHTML = `<td>${{run.id}}</td><td>${{run.name}}</td><td>${{run.source_file}}</td>`;
                tr.addEventListener('click', () => displayEvents(run));
                runsTableBody.appendChild(tr);
            }});
        }}
        function displayEvents(run) {{
            if (!run.events || run.events.length === 0) {{
                eventsContainer.innerHTML = `<p>No hay eventos para este run.</p>`;
                return;
            }}
            const html = run.events.map((ev, i) => {{
                const evStr = typeof ev === 'object' ? JSON.stringify(ev, null, 2) : String(ev);
                return `<div class='event-item'><strong>Evento ${{i+1}}:</strong><pre>${{evStr}}</pre></div>`;
            }}).join('');
            eventsContainer.innerHTML = html;
        }}
        // Render al cargar
        renderRuns();
    </script>
</body>
</html>
"""
        # Escribir archivo
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_template, encoding='utf-8')
        return {"ok": True, "output_path": str(output_path), "runs_count": len(runs)}
    except Exception as e:
        return {"ok": False, "error": str(e)}