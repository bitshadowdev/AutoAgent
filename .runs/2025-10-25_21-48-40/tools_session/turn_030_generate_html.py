import os
import json
from pathlib import Path

def generate_html(args: dict) -> dict:
    """Genera HTML que muestra los runs y sus eventos.
    Args:
        args: dict con claves:
            - core_path: ruta al directorio 'coreee' (no usado directamente en este ejemplo, pero se verifica su existencia).
            - runs_path: ruta al directorio '.runs' que contiene archivos JSON con la información de los runs.
    Returns:
        dict con claves:
            - ok: bool
            - html: str (el contenido HTML) si ok es True
            - error: mensaje si ok es False
    """
    try:
        core_path = Path(args.get('core_path', ''))
        runs_path = Path(args.get('runs_path', ''))
        # Verificar existencia de los directorios
        if not core_path.is_dir():
            return {'ok': False, 'error': f"Directorio core_path no encontrado: {core_path}"}
        if not runs_path.is_dir():
            return {'ok': False, 'error': f"Directorio runs_path no encontrado: {runs_path}"}

        # Recoger información de los archivos de runs (se asume JSON)
        runs = []
        for file in runs_path.iterdir():
            if file.is_file() and file.suffix.lower() in {'.json', '.js'}:
                try:
                    content = file.read_text(encoding='utf-8')
                    data = json.loads(content)
                except Exception as e:
                    # Si no es JSON válido, guardamos el texto bruto
                    data = {'raw': content, 'error': str(e)}
                runs.append({
                    'file_name': file.name,
                    'data': data
                })
        # Construir HTML
        # Convertir runs a JSON para usar en JavaScript (escapado)
        runs_json = json.dumps(runs, ensure_ascii=False, indent=2)
        html = f"""
<!DOCTYPE html>
<html lang='es'>
<head>
    <meta charset='UTF-8'>
    <title>Visor de Runs y Eventos</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        tr:hover {{ background-color: #f5f5f5; cursor: pointer; }}
        .event-list {{ margin-top: 10px; display: none; }}
        .event-list ul {{ list-style-type: disc; margin-left: 20px; }}
        .selected {{ background-color: #e0ffe0; }}
    </style>
</head>
<body>
    <h1>Runs detectados</h1>
    <table id='runsTable'>
        <thead>
            <tr><th>Archivo</th><th>Resumen</th></tr>
        </thead>
        <tbody></tbody>
    </table>
    <div id='eventContainer'></div>
    <script>
        const runs = {runs_json};
        const tbody = document.querySelector('#runsTable tbody');
        const eventContainer = document.getElementById('eventContainer');
        function createRow(run, index) {{
            const tr = document.createElement('tr');
            const tdFile = document.createElement('td');
            tdFile.textContent = run.file_name;
            const tdSummary = document.createElement('td');
            // Mostrar una breve descripción (primeros 60 chars del JSON)
            const summary = JSON.stringify(run.data).substring(0, 60) + '...';
            tdSummary.textContent = summary;
            tr.appendChild(tdFile);
            tr.appendChild(tdSummary);
            tr.addEventListener('click', () => showEvents(run, tr));
            return tr;
        }}
        function showEvents(run, rowElement) {{
            // Resaltar fila seleccionada
            document.querySelectorAll('#runsTable tr').forEach(r => r.classList.remove('selected'));
            rowElement.classList.add('selected');
            // Limpiar contenedor previo
            eventContainer.innerHTML = '';
            const title = document.createElement('h2');
            title.textContent = `Eventos de ${run.file_name}`;
            eventContainer.appendChild(title);
            // Intentar obtener una lista de eventos
            let events = [];
            if (Array.isArray(run.data.events)) {{
                events = run.data.events;
            }} else if (Array.isArray(run.data)) {{
                events = run.data;
            }} else if (run.data.events) {{
                events = [run.data.events];
            }} else {{
                events = [];
            }}
            if (events.length === 0) {{
                const p = document.createElement('p');
                p.textContent = 'No se encontraron eventos estructurados.';
                eventContainer.appendChild(p);
                return;
            }}
            const ul = document.createElement('ul');
            events.forEach((ev, i) => {{
                const li = document.createElement('li');
                // Si el evento es objeto, lo convertimos a string breve
                if (typeof ev === 'object') {{
                    li.textContent = JSON.stringify(ev);
                }} else {{
                    li.textContent = String(ev);
                }}
                ul.appendChild(li);
            }});
            eventContainer.appendChild(ul);
        }}
        // Poblar tabla
        runs.forEach((run, idx) => {{
            const row = createRow(run, idx);
            tbody.appendChild(row);
        }});
    </script>
</body>
</html>
"""
        return {'ok': True, 'html': html}
    except Exception as exc:
        return {'ok': False, 'error': str(exc)}
