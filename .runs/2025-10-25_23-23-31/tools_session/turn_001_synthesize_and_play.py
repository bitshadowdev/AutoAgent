import os
import json
import subprocess
import sys
import base64
import requests

# Aseguramos que playsound esté instalado
try:
    from playsound import playsound
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', 'playsound==1.3.0'])
    from playsound import playsound

def synthesize_and_play(args: dict) -> dict:
    """Genera audio con ElevenLabs y lo reproduce.
    Args:
        args: {
            "api_key": "string",  # clave de ElevenLabs
            "text": "string",     # texto a convertir a voz
            "voice_id": "string" (opcional)  # id de voz, default "EXAVITQu4vr4xnSDxMaL"
        }
    Returns:
        dict con {'ok': True, 'message': ..., 'file_path': ...} o {'ok': False, 'error': ...}
    """
    try:
        api_key = args.get('api_key')
        text = args.get('text', 'Hola mundo')
        voice_id = args.get('voice_id', 'EXAVITQu4vr4xnSDxMaL')
        if not api_key:
            return {'ok': False, 'error': 'api_key es requerido'}

        url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
        headers = {
            'Accept': 'audio/mpeg',
            'Content-Type': 'application/json',
            'xi-api-key': api_key,
        }
        data = {
            'text': text,
            'model_id': 'eleven_monolingual_v1',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.75
            }
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error en API ElevenLabs: {response.status_code} {response.text}'}
        audio_bytes = response.content

        # Guardamos archivo temporal
        tmp_dir = os.path.join(os.path.expanduser('~'), '.elevenlabs_tmp')
        os.makedirs(tmp_dir, exist_ok=True)
        file_path = os.path.join(tmp_dir, 'hola_mundo.mp3')
        with open(file_path, 'wb') as f:
            f.write(audio_bytes)

        # Reproducimos el audio
        playsound(file_path)

        return {'ok': True, 'message': 'Audio reproducido correctamente', 'file_path': file_path}
    except Exception as e:
        return {'ok': False, 'error': str(e)}