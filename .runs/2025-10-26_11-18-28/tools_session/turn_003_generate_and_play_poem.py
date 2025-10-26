import os
import json
import requests
import tempfile
import subprocess
import sys

def _install_package(package_name):
    try:
        __import__(package_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

# Ensure fallback packages are available
_install_package('gtts')
_install_package('playsound')

from gtts import gTTS
from playsound import playsound

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo sintetiza con ElevenLabs o gTTS y lo reproduce.
    Args:
        args: dict con clave 'api_key' (str) opcionalmente 'voice_id' (str).
    Returns:
        dict con 'ok': bool, 'message': str, 'audio_path': str (si ok).
    """
    api_key = args.get('api_key')
    if not api_key:
        return {'ok': False, 'error': 'api_key no suministrada'}
    voice_id = args.get('voice_id', 'EXAVITQu4vr4xnSDxMaL')

    # Paso 1: Verificar la clave con una petición ligera
    headers = {
        'xi-api-key': api_key,
        'Accept': 'application/json'
    }
    try:
        test_resp = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers, timeout=10)
        if test_resp.status_code != 200:
            return {'ok': False, 'error': f'Clave ElevenLabs inválida o insuficiente (status {test_resp.status_code})', 'detail': test_resp.text}
    except Exception as e:
        return {'ok': False, 'error': 'Error al validar la clave ElevenLabs', 'exception': str(e)}

    # Paso 2: Generar el poema (texto estático por simplicidad)
    poema = (
        "En la noche silente, la luna vigila,\n"
        "susurros de estrellas, la sombra destila.\n"
        "El viento recita en notas de plata,\n"
        "y el sueño despierta en la tierra helada."
    )

    # Paso 3: Intentar TTS con ElevenLabs
    tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    tts_headers = {
        'xi-api-key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg'
    }
    payload = {
        'text': poema,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
    audio_path = None
    try:
        resp = requests.post(tts_url, headers=tts_headers, json=payload, timeout=30)
        if resp.status_code == 200:
            # Guardar audio temporario
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tmp_file.write(resp.content)
            tmp_file.close()
            audio_path = tmp_file.name
        else:
            # Fallback a gTTS
            raise Exception(f'ElevenLabs returned status {resp.status_code}: {resp.text}')
    except Exception as e:
        # Fallback usando gTTS
        try:
            tts = gTTS(text=poema, lang='es')
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(tmp_file.name)
            audio_path = tmp_file.name
        except Exception as e2:
            return {'ok': False, 'error': 'Falló TTS con ElevenLabs y gTTS', 'exception': str(e2)}

    # Paso 4: Reproducir audio
    try:
        if audio_path:
            playsound(audio_path)
            return {'ok': True, 'message': 'Poema reproducido', 'audio_path': audio_path}
        else:
            return {'ok': False, 'error': 'No se generó archivo de audio'}
    except Exception as e:
        return {'ok': False, 'error': 'Error al reproducir audio', 'exception': str(e), 'audio_path': audio_path}
