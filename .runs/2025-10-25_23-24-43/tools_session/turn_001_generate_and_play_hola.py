import os
import json
import requests
import tempfile
import subprocess
import sys

def generate_and_play_hola(args: dict) -> dict:
    """Genera "Hola Mundo" con ElevenLabs y lo reproduce.
    args debe contener la clave API bajo la clave 'api_key'.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'api_key no provista'}
        # Texto a sintetizar
        text = 'Hola Mundo'
        # Voice ID predeterminada (puedes cambiarla si lo deseas)
        voice_id = 'EXAVITQu4vr4xnSDxMaL'
        url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
        headers = {
            'xi-api-key': api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            'text': text,
            'model_id': 'eleven_monolingual_v1',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.75
            }
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error del API: {response.status_code} {response.text}'}
        # Guardar audio en archivo temporal
        tmp_dir = tempfile.gettempdir()
        file_path = os.path.join(tmp_dir, 'hola_mundo.wav')
        with open(file_path, 'wb') as f:
            f.write(response.content)
        # Reproducir audio usando el reproductor del sistema
        # Intentamos usar ffplay (parte de ffmpeg) o el comando 'afplay' en macOS, o 'powershell' en Windows.
        try:
            if sys.platform.startswith('darwin'):
                subprocess.run(['afplay', file_path], check=True)
            elif sys.platform.startswith('win'):
                # PowerShell -Command (Add-Type …) para reproducir WAV
                subprocess.run([
                    'powershell', '-c',
                    f'(New-Object Media.SoundPlayer "{file_path}").PlaySync()'
                ], check=True)
            else:
                # Linux: intentar con ffplay (silencioso) o aplay
                if shutil.which('ffplay'):
                    subprocess.run(['ffplay', '-nodisp', '-autoexit', file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                elif shutil.which('aplay'):
                    subprocess.run(['aplay', file_path], check=True)
                else:
                    return {'ok': False, 'error': 'No se encontró un reproductor de audio disponible'}
        except Exception as e:
            return {'ok': False, 'error': f'Error al reproducir audio: {str(e)}'}
        return {'ok': True, 'file_path': file_path, 'message': 'Audio reproducido correctamente'}
    except Exception as exc:
        return {'ok': False, 'error': str(exc)}