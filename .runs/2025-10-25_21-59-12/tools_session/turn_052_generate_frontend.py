import os
from pathlib import Path
import json

def generate_frontend(args: dict) -> dict:
    """Genera un frontend HTML que muestra los archivos Python de coreee y los datos JSON de .runs.
    Argumentos esperados en `args`:
        - core_path (str): ruta al directorio `coreee`.
        - runs_path (str): ruta al directorio `.runs`.
        - output_path (str): ruta donde se guardará el HTML generado.
    Devuelve un dict con `ok` y, si es True, `output_path`; en caso de error, `error`.
    """
    core_path = args.get('core_path')
    runs_path = args.get('runs_path')
    output_path = args.get('output_path')
    try:
        # --- leer archivos .py de coreee -------------------------------------------------
        core_files = {}
        for py_file in Path(core_path).rglob('*.py'):
            rel = py_file.relative_to(core_path).as_posix()
            core_files[rel] = py_file.read_text(encoding='utf-8')
        # --- leer archivos .json de .runs ------------------------------------------------
        runs_data = []
        for json_file in Path(runs_path).rglob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    runs_data.append(json.load(f))
            except Exception:
                # Si no es JSON válido lo omitimos
                continue
        # --- generar HTML ---------------------------------------------------------------
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<title>AutoAgent Frontend</title>",
            "<style>",
            "body{font-family:Arial,Helvetica,sans-serif;margin:20px;}",
            "h2{margin-top:30px;}",
            "pre{background:#f9f9f9;padding:10px;overflow:auto;}",
            "table{border-collapse:collapse;width:100%;margin-top:10px;}",
            "th,td{border:1px solid #ddd;padding:8px;vertical-align:top;}",
            "tr:hover{background:#f1f1f1;}",
            "</style>",
            "</head>",
            "<body>",
            "<h1>AutoAgent Frontend</h1>",
            "<h2>Core Files (Python)</h2>"
        ]
        # añadir cada archivo .py
        for rel_path, content in core_files.items():
            html_parts.append(f"<h3>{rel_path}</h3>")
            html_parts.append(f"<pre>{content}</pre>")
        # tabla de runs
        html_parts.extend([
            "<h2>.runs Data (JSON)</h2>",
            "<table>",
            "<thead><tr><th>#</th><th>Run JSON</th></tr></thead>",
            "<tbody>"
        ])
        for idx, run in enumerate(runs_data):
            pretty = json.dumps(run, indent=2, ensure_ascii=False)
            html_parts.append(f"<tr><td>{idx+1}</td><td><pre>{pretty}</pre></td></tr>")
        html_parts.extend(["</tbody>", "</table>", "</body>", "</html>"])
        html_content = "\n".join(html_parts)
        # escribir archivo
        Path(output_path).write_text(html_content, encoding='utf-8')
        return {"ok": True, "output_path": output_path}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}