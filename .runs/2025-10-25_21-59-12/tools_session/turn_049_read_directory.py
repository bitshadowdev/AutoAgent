import os
import json

def read_directory(args: dict) -> dict:
    """Lee recursivamente todos los archivos de texto dentro del directorio especificado.
    Args:
        args: {'path': str} Ruta del directorio a leer.
    Returns:
        dict con {'ok': bool, 'files': dict} donde 'files' mapea ruta completa -> contenido del archivo (texto).
    """
    path = args.get('path')
    if not path:
        return {'ok': False, 'error': 'Missing path argument'}
    files_content = {}
    try:
        for root, _, files in os.walk(path):
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as fp:
                        files_content[fpath] = fp.read()
                except Exception as e:
                    files_content[fpath] = f'<error reading file: {e}>'
        return {'ok': True, 'files': files_content}
    except Exception as e:
        return {'ok': False, 'error': str(e)}