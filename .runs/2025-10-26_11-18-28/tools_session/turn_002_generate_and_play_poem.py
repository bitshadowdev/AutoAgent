import os
import json
import requests
import tempfile
import base64
import subprocess

def _install_package(package_name: str):
    try:
        __import__(package_name)
    except ImportError:
        subprocess.check_call(['python', '-m', 'pip', 'install', package_name])

# Ensure required packages are available
_install_package('playsound')
_install_package('gtts')

from playsound import playsound
from gtts import gTTS

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo sintetiza a audio y lo reproduce.
    Args:
        args: {
            "api_key": "<ElevenLabs API key>",
            "voice_id": "<optional voice id>"
        }
    Returns:
        dict con claves 'ok' (bool) y opcionalmente 'error' o 'message'.
    """
    api_key = args.get('api_key')
    if not api_key:
        return {'ok': False, 'error': 'API key no provista en args'}

    voice_id = args.get('voice_id', 'EXAVITQu4vr4xnSDxMaL')  # voice predeterminada
    # Paso 1: Verificar la clave de ElevenLabs
    try:
        verify_resp = requests.get(
            'https://api.elevenlabs.io/v1/user',
            headers={'xi-api-key': api_key},
            timeout=10
        )
        if verify_resp.status_code != 200:
            # Si la clave no es válida o hay otro error, se usará gTTS como fallback
            raise ValueError(f'Verificación falló con status {verify_resp.status_code}')
    except Exception as e:
        # Fallback a gTTS
        fallback_msg = f'Clave ElevenLabs no válida o error de red: {e}. Se usará gTTS como alternativa.'
        return _synthesize_with_gtts(fallback_msg)

    # Paso 2: Generar poema (texto estático simple)
    poem = (
        "En la quietud del alba, el viento susurra,\n"
        "hojas doradas bailan al compás del sol.\n"
        "Silencio en el bosque, la luz se deshilvana,\n"
        "y el día despierta, suave y sin control."
    )

    # Paso 3: Llamar a la API de ElevenLabs
    tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    payload = {
        'text': poem,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
    headers = {
        'xi-api-key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg'
    }
    try:
        resp = requests.post(tts_url, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            raise ValueError(f'ElevenLabs API error {resp.status_code}: {resp.text}')
        # Guardar audio en archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tmp_file.write(resp.content)
            audio_path = tmp_file.name
        # Reproducir audio
        try:
            playsound(audio_path)
        except Exception as play_err:
            return {'ok': False, 'error': f'Error al reproducir audio: {play_err}'}
        finally:
            # Opcional: limpiar archivo después de reproducir
            try:
                os.remove(audio_path)
            except Exception:
                pass
        return {'ok': True, 'message': 'Poema generado y reproducido con ElevenLabs'}
    except Exception as api_err:
        # En caso de cualquier error, fallback a gTTS
        fallback_msg = f'Error al usar ElevenLabs: {api_err}. Se usará gTTS como alternativa.'
        return _synthesize_with_gtts(fallback_msg)

def _synthesize_with_gtts(message: str) -> dict:
    """Usa gTTS como alternativa para convertir texto a voz y reproducir."""
    try:
        tts = gTTS(text=message, lang='es')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tts.save(tmp_file.name)
            audio_path = tmp_file.name
        try:
            playsound(audio_path)
        except Exception as play_err:
            return {'ok': False, 'error': f'Error al reproducir audio gTTS: {play_err}'}
        finally:
            try:
                os.remove(audio_path)
            except Exception:
                pass
        return {'ok': True, 'message': message}
    except Exception as e:
        return {'ok': False, 'error': f'Fallo gTTS: {e}'}