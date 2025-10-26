import subprocess
import json

def run_command(args: dict) -> dict:
    """Ejecuta un comando del sistema y devuelve la salida.
    args debe contener la clave 'command' con el comando a ejecutar como cadena.
    """
    try:
        cmd = args.get('command')
        if not cmd:
            return {'ok': False, 'error': 'No se proporcionó el comando a ejecutar.'}
        # Ejecutar el comando
        completed = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        result = {
            'ok': completed.returncode == 0,
            'returncode': completed.returncode,
            'stdout': completed.stdout.strip(),
            'stderr': completed.stderr.strip()
        }
        return result
    except Exception as e:
        return {'ok': False, 'error': str(e)}