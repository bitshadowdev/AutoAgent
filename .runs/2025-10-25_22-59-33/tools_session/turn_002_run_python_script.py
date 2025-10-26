import subprocess, tempfile, os, sys, json, textwrap

def run_python_script(args: dict) -> dict:
    """Ejecuta código Python provisto en 'code' y devuelve la salida.
    Args:
        args: {'code': str}
    Returns:
        dict con 'ok': bool, 'output': str (stdout+stderr) o 'error': str
    """
    try:
        code = args.get('code')
        if not isinstance(code, str):
            return {'ok': False, 'error': 'El argumento "code" debe ser una cadena.'}
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.py') as tmp:
            tmp_path = tmp.name
            # Asegurarse de que la indentación sea correcta
            tmp.write(textwrap.dedent(code))
        # Ejecutar el script
        result = subprocess.run([sys.executable, tmp_path], capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        # Limpiar archivo temporal
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        return {'ok': True, 'output': output}
    except subprocess.TimeoutExpired:
        return {'ok': False, 'error': 'Ejecución del script superó el tiempo límite.'}
    except Exception as e:
        return {'ok': False, 'error': f'Excepción inesperada: {e}'}