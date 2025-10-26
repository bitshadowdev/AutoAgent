import os
import json

def read_directory_recursive(args: dict) -> dict:
    """Lee recursivamente todos los archivos de texto bajo el directorio especificado.

    Args:
        args (dict): {
            "path": "ruta del directorio a leer"
        }
    Returns:
        dict: {
            "ok": bool,
            "error": str (opcional),
            "files": [
                {"relative_path": str, "content": str},
                ...
            ]
        }
    """
    try:
        base_path = args.get('path')
        if not base_path:
            return {"ok": False, "error": "'path' es obligatorio"}
        if not os.path.isdir(base_path):
            return {"ok": False, "error": f"El path '{base_path}' no es un directorio válido"}
        result = []
        for root, _, files in os.walk(base_path):
            for fname in files:
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, base_path)
                # Intentar leer como texto UTF-8, si falla se ignora el archivo
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception:
                    # Saltar binarios o archivos con encoding distinto
                    continue
                result.append({"relative_path": rel_path.replace('\\', '/'), "content": content})
        return {"ok": True, "files": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}