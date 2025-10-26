import os
import json
import requests
import subprocess
import tempfile

def generate_and_play_hola_mundo(args: dict) -> dict:
    """Genera "Hola mundo" con ElevenLabs y reproduce el audio.
    Args:
        args: {
            "api_key": "string"  # clave API de ElevenLabs
        }
    Returns:
        dict con {'ok': bool, 'file': ruta_al_mp3, 'error': str (si falla)}
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'api_key no proporcionada'}
        # Voice ID de "Rachel" (puede usarse cualquier voz disponible)
        voice_id = '21m00Tcm4TlvDq8ikWAM'
        url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
        headers = {
            'xi-api-key': api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            'text': 'Hola mundo',
            'model_id': 'eleven_monolingual_v1',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.75
            }
        }
        # Solicitar el audio en formato MP3
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error API ElevenLabs: {response.status_code} {response.text}'}
        # Guardar el audio en un archivo temporal
        tmp_dir = tempfile.gettempdir()
        file_path = os.path.join(tmp_dir, 'hola_mundo.mp3')
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        # Intentar reproducir el audio usando ffplay (si está disponible)
        try:
            subprocess.run(['ffplay', '-nodisp', '-autoexit', file_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            # ffplay no está instalado; intentar con playsound (instalar dinámicamente)
            try:
                import importlib.util
                if importlib.util.find_spec('playsound') is None:
                    subprocess.run([sys.executable, '-m', 'pip', 'install', 'playsound'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                from playsound import playsound
                playsound(file_path)
            except Exception as e:
                # No se pudo reproducir, pero el archivo se generó
                return {'ok': True, 'file': file_path, 'error': f'Audio generado pero no se pudo reproducir automáticamente: {e}'}
        return {'ok': True, 'file': file_path}
    except Exception as e:
        return {'ok': False, 'error': str(e)}