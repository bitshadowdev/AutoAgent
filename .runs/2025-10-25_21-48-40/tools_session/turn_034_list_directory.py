import os, json

def list_directory(args: dict) -> dict:
    """Devuelve la lista de nombres de archivo (y carpetas) dentro de `path`.
    Args:
        args (dict): {'path': str}
    Returns:
        dict: {'ok': bool, 'files': list[str], 'error': str (optional)}
    """
    try:
        path = args.get('path')
        if not path:
            return {'ok': False, 'error': 'Falta el parámetro "path"'}
        if not os.path.isdir(path):
            return {'ok': False, 'error': f'La ruta no es un directorio: {path}'}
        files = os.listdir(path)
        return {'ok': True, 'files': files}
    except Exception as e:
        return {'ok': False, 'error': str(e)}