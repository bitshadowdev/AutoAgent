import os
import json
import sys
import subprocess
import tempfile
from pathlib import Path
import requests

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo convierte a audio y lo reproduce.
    Parámetros esperados en args:
        - api_key (str): clave de ElevenLabs.
    Devuelve:
        dict con claves 'ok' (bool) y, en caso de error, 'error' y opcionalmente 'exception'.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'Falta la API key en los argumentos.'}

        headers = {
            'xi-api-key': api_key,
            'Content-Type': 'application/json'
        }

        # 1. Verificación ligera de la clave (lista de voces)
        try:
            resp_check = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers, timeout=10)
        except Exception as e:
            return {'ok': False, 'error': 'No se pudo contactar ElevenLabs para validar la clave.', 'exception': str(e)}
        if resp_check.status_code == 401:
            return {'ok': False, 'error': 'Clave ElevenLabs inválida (401 Unauthorized).'}
        if resp_check.status_code == 403:
            return {'ok': False, 'error': 'Acceso denegado a ElevenLabs (403 Forbidden).'}
        if resp_check.status_code >= 400:
            return {'ok': False, 'error': f'Error al validar la clave: HTTP {resp_check.status_code}', 'detail': resp_check.text}

        # 2. Generar poema en texto (simple ejemplo)
        poema = (
            "En la quietud de la noche, la luna silente,\n"
            "baila entre sombras, susurros de estrellas,\n"
            "el viento acaricia la tierra dormida,\n"
            "y el sueño se vuelve poema eterno."
        )

        # 3. Intentar TTS con ElevenLabs
        voice_id = 'EXAVITQu4vr4xnSDxMaL'  # voz por defecto
        tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream'
        payload = {
            'text': poema,
            'model_id': 'eleven_multilingual_v2',
            'voice_settings': {}
        }
        try:
            resp_tts = requests.post(tts_url, headers={**headers, 'Accept': 'audio/mpeg'}, json=payload, timeout=30)
        except Exception as e:
            resp_tts = None
            tts_error = str(e)
        audio_path = None
        if resp_tts and resp_tts.status_code == 200:
            # Guardar audio
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            audio_path = temp_file.name
            with open(audio_path, 'wb') as f:
                f.write(resp_tts.content)
        else:
            # 4. Fallback a gTTS si ElevenLabs falla
            try:
                from gtts import gTTS
            except Exception:
                # intentar instalar gtts
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'gtts', '--quiet'])
                    from gtts import gTTS
                except Exception as e:
                    return {'ok': False, 'error': 'No se pudo instalar o importar gTTS para fallback.', 'exception': str(e)}
            try:
                tts = gTTS(text=poema, lang='es')
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                audio_path = temp_file.name
                tts.save(audio_path)
            except Exception as e:
                return {'ok': False, 'error': 'Error al generar audio con gTTS.', 'exception': str(e)}

        if not audio_path or not os.path.isfile(audio_path):
            return {'ok': False, 'error': 'Archivo de audio no fue creado.'}

        # 5. Reproducir audio con playsound (instalar si falta)
        try:
            from playsound import playsound
        except Exception:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'playsound', '--quiet'])
                from playsound import playsound
            except Exception as e:
                return {'ok': False, 'error': 'No se pudo instalar o importar playsound.', 'exception': str(e)}
        try:
            playsound(audio_path)
        except Exception as e:
            return {'ok': False, 'error': 'Error al reproducir el audio.', 'exception': str(e), 'audio_path': audio_path}

        return {'ok': True, 'message': 'Poema generado y reproducido exitosamente.', 'audio_path': audio_path}
    except Exception as e:
        return {'ok': False, 'error': 'Excepción inesperada en la herramienta.', 'exception': str(e)}
