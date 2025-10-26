import requests
import os

def download_and_save(args: dict) -> dict:
    """Descarga el contenido de una URL y lo guarda en un archivo.
    Args:
        args: {
            "url": "http://...",   # URL a descargar
            "output_path": "ruta/archivo.html"  # ruta del archivo donde guardar
        }
    Returns:
        dict con {'ok': True, 'output_path': ..., 'status_code': ...} o {'ok': False, 'error': ...}
    """
    url = args.get('url')
    output_path = args.get('output_path')
    if not url or not output_path:
        return {'ok': False, 'error': 'Faltan parámetros url u output_path'}
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        # Asegurarse de que el directorio exista
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        return {'ok': True, 'output_path': os.path.abspath(output_path), 'status_code': response.status_code}
    except Exception as e:
        return {'ok': False, 'error': str(e)}