import os
import json
import sys
import tempfile
import subprocess
import importlib
import importlib.util

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests

def _ensure_package(package_name):
    """Instala el paquete con pip si no está disponible y lo importa."""
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])
    return importlib.import_module(package_name)

def _install_and_import(package_name):
    try:
        return __import__(package_name)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])
        return __import__(package_name)

def _validate_elevenlabs_key(api_key):
    """Realiza una petición ligera para comprobar si la clave es válida.
    Devuelve (True, None) si está bien, o (False, mensaje_error) si no."""
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    try:
        resp = requests.get('https://api.elevenlabs.io/v1/models', headers=headers, timeout=10)
        if resp.status_code == 200:
            return True, None
        elif resp.status_code == 401:
            return False, 'Clave de ElevenLabs inválida (401 Unauthorized).'
        elif resp.status_code == 403:
            return False, 'Clave de ElevenLabs no tiene permiso (403 Forbidden).'
        else:
            return False, f'Error inesperado al validar la clave: HTTP {resp.status_code}.'
    except Exception as e:
        return False, f'Excepción al validar la clave: {str(e)}'

def _synthesize_elevenlabs(text, api_key):
    """Intenta generar audio con ElevenLabs. Devuelve bytes del MP3 o None si falla."""
    # Usamos una voice_id pública (Rachel) para demostrar.
    voice_id = 'EXAVITQu4vr4xnSDxMaL'
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        'text': text,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            return resp.content
        else:
            # Devolver None para que el fallback se active.
            return None
    except Exception:
        return None

def _synthesize_gtts(text):
    """Genera MP3 usando gTTS. Devuelve bytes del MP3 o lanza excepción."""
    gtts = _install_and_import('gtts')
    from io import BytesIO
    mp3_fp = BytesIO()
    tts = gtts.gTTS(text=text, lang='es')
    tts.write_to_fp(mp3_fp)
    return mp3_fp.getvalue()

def _play_audio(file_path):
    """Reproduce el archivo MP3 usando playsound. Maneja errores y devuelve True/False."""
    playsound = _install_and_import('playsound')
    try:
        # playsound acepta la ruta tal cual, sin comillas.
        playsound.playsound(file_path, True)
        return True, None
    except Exception as e:
        return False, str(e)

def generate_and_play_poem(args):
    """Genera un poema en texto, lo convierte a audio y lo reproduce.
    Parámetros esperados en *args*:
        - api_key (str): clave de ElevenLabs.
    Retorna dict con 'ok' y, en caso de error, 'error' y detalles.
    """
    api_key = args.get('api_key')
    if not api_key:
        return {'ok': False, 'error': 'Falta la clave API en los argumentos.'}

    # 1. Poema estático (puede generarse dinámicamente si se desea).
    poem = (
        "En la quietud de la noche,\n"
        "las estrellas susurran secretos,\n"
        "el viento lleva recuerdos,\n"
        "y el alma busca su reflejo."
    )

    # 2. Validar la clave antes de intentar usar ElevenLabs.
    valid, validation_msg = _validate_elevenlabs_key(api_key)
    audio_bytes = None
    if valid:
        audio_bytes = _synthesize_elevenlabs(poem, api_key)
        if audio_bytes is None:
            # Falló la síntesis, usaremos fallback.
            fallback_reason = 'Falló la síntesis con ElevenLabs.'
        else:
            fallback_reason = None
    else:
        fallback_reason = validation_msg

    # 3. Si no hay audio_bytes, usar gTTS fallback.
    if audio_bytes is None:
        try:
            audio_bytes = _synthesize_gtts(poem)
        except Exception as e:
            return {
                'ok': False,
                'error': 'No se pudo generar el audio con gTTS.',
                'exception': str(e),
                'fallback_reason': fallback_reason
            }

    # 4. Guardar MP3 a archivo temporal.
    try:
        tmp_dir = tempfile.gettempdir()
        tmp_file = os.path.join(tmp_dir, f'poem_{next(tempfile._get_candidate_names())}.mp3')
        with open(tmp_file, 'wb') as f:
            f.write(audio_bytes)
        audio_path = os.path.abspath(tmp_file)
    except Exception as e:
        return {'ok': False, 'error': 'Error al escribir el archivo de audio.', 'exception': str(e)}

    # 5. Reproducir audio.
    played, play_err = _play_audio(audio_path)
    if not played:
        return {
            'ok': False,
            'error': 'Error al reproducir el audio.',
            'exception': play_err,
            'audio_path': audio_path
        }

    return {'ok': True, 'message': 'Poema reproducido exitosamente.', 'audio_path': audio_path}
