import os
import json
import tempfile
import requests

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo convierte a audio y lo reproduce.
    Parámetros esperados en *args*:
        - api_key (str): clave de ElevenLabs.
    Devuelve un dict JSON‑serializable con los campos:
        - ok (bool)
        - error (str, opcional)
        - status (int, opcional)
        - audio_path (str, opcional)
        - fallback_used (bool, opcional)
    """
    # ---------- Validación de argumentos ----------
    api_key = args.get('api_key')
    if not api_key:
        return {'ok': False, 'error': 'Missing api_key argument'}

    # ---------- Verificar dependencias ----------
    try:
        from playsound import playsound
    except Exception as e:
        return {'ok': False, 'error': 'playsound library not available', 'exception': str(e)}
    try:
        from gtts import gTTS
        gtts_available = True
    except Exception:
        gtts_available = False

    # ---------- Paso 1: validar la API key con un request ligero ----------
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }
    try:
        resp = requests.get('https://api.elevenlabs.io/v1/models', headers=headers, timeout=10)
    except Exception as e:
        return {'ok': False, 'error': 'Error al contactar ElevenLabs', 'exception': str(e)}
    if resp.status_code != 200:
        # 401/403 u otro error -> abortar temprano
        return {
            'ok': False,
            'error': f'Clave API de ElevenLabs inválida o sin permisos (status {resp.status_code})',
            'status': resp.status_code,
            'detail': resp.text
        }

    # ---------- Paso 2: generar poema (texto estático) ----------
    poem = (
        "En la quietud del alba, susurra el viento,\n"
        "Pintando en el cielo luces de intento.\n"
        "Las hojas cantan su canción dorada,\n"
        "Y el día despierta, vida renovada."
    )

    # ---------- Paso 3: intentar TTS con ElevenLabs ----------
    voice_id = 'EXAVITQu4vr4xnSDxMaL'  # voz por defecto de ElevenLabs
    tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    payload = {
        'text': poem,
        'model_id': 'eleven_multilingual_v2',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
    headers_tts = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg'
    }
    audio_path = None
    fallback_used = False
    try:
        r = requests.post(tts_url, headers=headers_tts, json=payload, timeout=30)
        if r.status_code == 200:
            # Guardar audio
            fd, tmp_path = tempfile.mkstemp(suffix='.mp3')
            os.close(fd)
            with open(tmp_path, 'wb') as f:
                f.write(r.content)
            audio_path = tmp_path
        else:
            # Si ElevenLabs falla, marcar para fallback
            fallback_used = True
    except Exception as e:
        fallback_used = True
        # continuar al fallback

    # ---------- Paso 4: fallback a gTTS si es necesario ----------
    if audio_path is None:
        if not gtts_available:
            return {'ok': False, 'error': 'gTTS no está disponible y ElevenLabs falló', 'fallback_used': True}
        try:
            tts = gTTS(text=poem, lang='es')
            fd, tmp_path = tempfile.mkstemp(suffix='.mp3')
            os.close(fd)
            tts.save(tmp_path)
            audio_path = tmp_path
            fallback_used = True
        except Exception as e:
            return {'ok': False, 'error': 'Error generando audio con gTTS', 'exception': str(e), 'fallback_used': True}

    # ---------- Paso 5: reproducir audio ----------
    try:
        abs_path = os.path.abspath(audio_path)
        playsound(abs_path)
    except Exception as e:
        return {
            'ok': False,
            'error': 'Error al reproducir el audio',
            'exception': str(e),
            'audio_path': audio_path,
            'fallback_used': fallback_used
        }

    return {
        'ok': True,
        'audio_path': audio_path,
        'fallback_used': fallback_used
    }
