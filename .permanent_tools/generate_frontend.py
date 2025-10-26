import os
import json
from pathlib import Path

def generate_frontend(args: dict) -> dict:
    """Genera un archivo HTML que lista los archivos y contenidos de los directorios
    especificados (core y runs). El HTML incluye secciones para los archivos de
    core y para cada run/evento encontrado.

    Parámetros esperados en `args`:
        - core_path: ruta al directorio donde está el código del agente.
        - runs_path: ruta al directorio con los archivos de ejecución/eventos.
        - output_path (opcional): ruta completa donde guardar el HTML generado.
    """
    try:
        core_path = Path(args.get('core_path'))
        runs_path = Path(args.get('runs_path'))
        output_path = Path(args.get('output_path', core_path.parent / 'frontend.html'))

        if not core_path.is_dir():
            return {'ok': False, 'error': f'core_path {core_path} no es un directorio válido'}
        if not runs_path.is_dir():
            return {'ok': False, 'error': f'runs_path {runs_path} no es un directorio válido'}

        # Recolectar información de archivos de core
        core_files = []
        for file_path in core_path.rglob('*'):
            if file_path.is_file():
                try:
                    content = file_path.read_text(errors='ignore')
                except Exception:
                    content = ''
                core_files.append({
                    'relative_path': str(file_path.relative_to(core_path)),
                    'size': file_path.stat().st_size,
                    'content': content[:500]  # preview limitado
                })

        # Recolectar información de runs/eventos
        run_files = []
        for file_path in runs_path.rglob('*'):
            if file_path.is_file():
                try:
                    # Intentamos parsear como JSON, si falla, lo tratamos como texto
                    text = file_path.read_text(errors='ignore')
                    try:
                        data = json.loads(text)
                        preview = json.dumps(data, indent=2)[:500]
                    except Exception:
                        preview = text[:500]
                except Exception:
                    preview = ''
                run_files.append({
                    'relative_path': str(file_path.relative_to(runs_path)),
                    'size': file_path.stat().st_size,
                    'preview': preview
                })

        # Construir HTML
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="es">',
            '<head>',
            '  <meta charset="UTF-8">',
            '  <title>Frontend AutoAgent</title>',
            '  <style>',
            '    body {font-family: Arial, sans-serif; margin: 20px; background:#f9f9f9;}',
            '    h2 {color:#333;}',
            '    .section {margin-bottom: 30px; padding:10px; background:#fff; border-radius:5px; box-shadow:0 2px 4px rgba(0,0,0,0.1);}',
            '    .file {margin:5px 0; padding:5px; border-bottom:1px solid #eee;}',
            '    .preview {font-family: monospace; white-space: pre-wrap; background:#f4f4f4; padding:5px; border-radius:3px; margin-top:5px;}',
            '  </style>',
            '</head>',
            '<body>',
            f'<h1>AutoAgent Frontend</h1>',
            '<div class="section">',
            f'<h2>Archivos del Core ({len(core_files)})</h2>'
        ]
        for f in core_files:
            html_parts.append(
                f'<div class="file"><strong>{f["relative_path"]}</strong> ({f["size"]} bytes)'
                f'<div class="preview">{f["content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}</div>'
                f'</div>'
            )
        html_parts.extend(['</div>', '<div class="section">', f'<h2>Runs y Eventos ({len(run_files)})</h2>'])
        for f in run_files:
            html_parts.append(
                f'<div class="file"><strong>{f["relative_path"]}</strong> ({f["size"]} bytes)'
                f'<div class="preview">{f["preview"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}</div>'
                f'</div>'
            )
        html_parts.extend(['</div>', '</body>', '</html>'])

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text('\n'.join(html_parts), encoding='utf-8')

        return {'ok': True, 'output_path': str(output_path), 'core_file_count': len(core_files), 'run_file_count': len(run_files)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}