import os

def read_file(args: dict) -> dict:
    """Lee el contenido de un archivo de texto y lo devuelve.
    Args:
        args (dict): debe contener la clave 'path' con la ruta del archivo.
    Returns:
        dict: {'ok': True, 'content': <texto del archivo>} o {'ok': False, 'error': <mensaje>}
    """
    try:
        path = args.get('path')
        if not path:
            return {'ok': False, 'error': 'Ruta no proporcionada'}
        # Seguridad básica: asegurarse de que el archivo exista y sea un archivo regular
        if not os.path.isfile(path):
            return {'ok': False, 'error': f'Archivo no encontrado: {path}'}
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {'ok': True, 'content': content}
    except Exception as e:
        return {'ok': False, 'error': str(e)}