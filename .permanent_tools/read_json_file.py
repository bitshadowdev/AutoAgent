import json
import os

def read_json_file(args: dict) -> dict:
    """Lee un archivo JSON, verifica su validez y devuelve una muestra del contenido.

    Args:
        args (dict): {'file_path': str}

    Returns:
        dict: {
            'ok': bool,
            'file_path': str,
            'num_records': int,
            'sample': list,
            'error': str (opcional)
        }
    """
    file_path = args.get('file_path')
    if not file_path:
        return {'ok': False, 'error': 'Parametro "file_path" es requerido.'}
    try:
        if not os.path.isfile(file_path):
            return {'ok': False, 'error': f'Archivo no encontrado: {file_path}'}
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Verificar que sea JSON válido
        data = json.loads(content)
        # Esperamos una lista de objetos
        if not isinstance(data, list):
            return {'ok': False, 'error': 'El JSON no contiene una lista en la raíz.'}
        num = len(data)
        # Tomar una muestra de los primeros 3 elementos (o menos)
        sample = data[:3]
        return {
            'ok': True,
            'file_path': file_path,
            'num_records': num,
            'sample': sample
        }
    except FileNotFoundError:
        return {'ok': False, 'error': f'Archivo no encontrado: {file_path}'}
    except json.JSONDecodeError as e:
        return {'ok': False, 'error': f'Error al decodificar JSON: {str(e)}'}
    except Exception as e:
        return {'ok': False, 'error': f'Error inesperado: {str(e)}'}