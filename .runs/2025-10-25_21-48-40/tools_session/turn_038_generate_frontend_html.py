import os
import json

def generate_frontend_html(args: dict) -> dict:
    """Genera un archivo HTML que muestra el código de los módulos en 'coreee' y los datos JSON de '.runs'.
    
    Parameters
    ----------
    args : dict
        - core_path (str): ruta absoluta al directorio 'coreee'.
        - runs_path (str): ruta absoluta al directorio '.runs'.
        - output_path (str): ruta donde se guardará el archivo HTML generado.
    
    Returns
    -------
    dict
        - ok (bool): True si se creó el archivo exitosamente.
        - output_path (str, optional): ruta del archivo HTML.
        - error (str, optional): mensaje de error en caso de fallo.
    """
    core_path = args.get('core_path')
    runs_path = args.get('runs_path')
    output_path = args.get('output_path')
    try:
        # --- leer archivos de coreee ---
        core_files = []
        for entry in os.listdir(core_path):
            full_path = os.path.join(core_path, entry)
            if os.path.isfile(full_path) and entry.lower().endswith('.py'):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                core_files.append({
                    'filename': entry,
                    'content': content
                })
        # --- leer archivos de .runs (asumimos JSON) ---
        runs_files = []
        for entry in os.listdir(runs_path):
            full_path = os.path.join(runs_path, entry)
            if os.path.isfile(full_path) and entry.lower().endswith('.json'):
                with open(full_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        # si no es JSON válido, leer como texto
                        f.seek(0)
                        data = f.read()
                runs_files.append({
                    'filename': entry,
                    'data': data
                })
        # --- construir HTML ---
        html_content = f"""
<!DOCTYPE html>
<html lang='es'>
<head>
    <meta charset='UTF-8'>
    <title>Frontend AutoAgent</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h2 {{ color: #2c3e50; }}
        .container {{ display: flex; gap: 20px; }}
        .list {{ width: 30%; overflow-y: auto; max-height: 80vh; border: 1px solid #ddd; padding: 10px; }}
        .detail {{ flex-grow: 1; border: 1px solid #ddd; padding: 10px; overflow-y: auto; max-height: 80vh; }}
        pre {{ background:#f8f8f8; padding:10px; overflow:auto; }}
        .item {{ cursor:pointer; padding:5px; border-bottom:1px solid #eee; }}
        .item:hover {{ background:#eaeaea; }}
    </style>
</head>
<body>
    <h1>Visor de Core y Runs</h1>
    <div class='container'>
        <div class='list' id='coreList'>
            <h2>Módulos Core</h2>
        </div>
        <div class='list' id='runsList'>
            <h2>Runs (JSON)</h2>
        </div>
        <div class='detail' id='detail'>
            <h2>Detalle</h2>
            <pre id='detailContent'>Seleccione un elemento para ver su contenido.</pre>
        </div>
    </div>
    <script>
        const coreFiles = {json.dumps(core_files, ensure_ascii=False)};
        const runsFiles = {json.dumps(runs_files, ensure_ascii=False)};
        const coreList = document.getElementById('coreList');
        const runsList = document.getElementById('runsList');
        const detailContent = document.getElementById('detailContent');
        function addItem(container, file, type) {{
            const div = document.createElement('div');
            div.className = 'item';
            div.textContent = file.filename;
            div.onclick = () => {{
                const data = type === 'core' ? file.content : JSON.stringify(file.data, null, 2);
                detailContent.textContent = data;
            }};
            container.appendChild(div);
        }}
        coreFiles.forEach(f => addItem(coreList, f, 'core'));
        runsFiles.forEach(f => addItem(runsList, f, 'run'));
    </script>
</body>
</html>
"""
        # escribir archivo
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as out_file:
            out_file.write(html_content)
        return {'ok': True, 'output_path': output_path}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
