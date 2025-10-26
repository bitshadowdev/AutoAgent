import os
import json

def read_project(args: dict) -> dict:
    """Recorre recursivamente el directorio especificado y devuelve un dict
    donde las claves son rutas relativas (usando '/' como separador) y los
    valores son el contenido del archivo como string.

    Parámetros esperados en *args*:
        - "path": (str) ruta absoluta del directorio a leer.
        - "extensions": (list, opcional) lista de extensiones que se deben
          incluir, por ejemplo [".py", ".json", ".txt"]. Si no se indica, se
          leerán todos los archivos de texto.
    """
    path = args.get('path')
    if not path:
        return {"ok": False, "error": "Missing 'path' argument"}
    extensions = args.get('extensions')
    result = {}
    try:
        for root, _, files in os.walk(path):
            for fname in files:
                # Determinar si la extensión está permitida
                if extensions is not None:
                    if not any(fname.lower().endswith(ext) for ext in extensions):
                        continue
                file_path = os.path.join(root, fname)
                rel_path = os.path.relpath(file_path, path).replace(os.sep, '/')
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    result[rel_path] = content
                except Exception as e:
                    # Si no se puede leer, almacenamos el error
                    result[rel_path] = f"<error reading file: {e}>"
        return {"ok": True, "files": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}
