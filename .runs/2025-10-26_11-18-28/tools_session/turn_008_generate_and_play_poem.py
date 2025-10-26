import os
import json
import requests
import tempfile
from pathlib import Path

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo convierte a audio (ElevenLabs con fallback a gTTS) y lo reproduce.
    Args:
        args: dict con la clave 'api_key' (str) de ElevenLabs.
    Returns:
        dict con clave 'ok' (bool) y, en caso de éxito, 'audio_path' (str).
        En caso de error, incluye 'error' y opcionalmente 'details'.
    """
    # Validar argumentos
    api_key = args.get('api_key')
    if not api_key:
        return {'ok': False, 'error': 'Falta la API key de ElevenLabs en los argumentos.'}

    # Funciones auxiliares
    def check_dependency(module_name, import_stmt):
        try:
            globals()[module_name] = __import__(module_name)
        except Exception as e:
            return False, f"Módulo '{module_name}' no está disponible: {e}"
        return True, None

    # Verificar dependencias críticas
    ok, msg = check_dependency('gtts', 'from gtts import gTTS')
    if not ok:
        return {'ok': False, 'error': msg}
    ok, msg = check_dependency('playsound', 'from playsound import playsound')
    if not ok:
        return {'ok': False, 'error': msg}
    from gtts import gTTS
    from playsound import playsound

    # 1. Verificar la API key de ElevenLabs (petición ligera)
    try:
        headers = {'Authorization': f'Bearer {api_key}'}
        resp = requests.get('https://api.elevenlabs.io/v1/models', headers=headers, timeout=10)
        if resp.status_code == 401:
            return {'ok': False, 'error': 'Clave API de ElevenLabs inválida o sin permisos.', 'status': 401}
        if resp.status_code != 200:
            return {'ok': False, 'error': f'Error al validar la API key de ElevenLabs: HTTP {resp.status_code}', 'status': resp.status_code}
    except Exception as e:
        return {'ok': False, 'error': f'Excepción al validar la API key: {e}'}

    # 2. Generar poema simple (texto estático)
    poem = (
        "En la quietud del alba, el silencio canta,\n"
        "las sombras del sueño se disipan en luz,\n"
        "y el viento susurra versos que el tiempo no quebranta,\n"
        "como hojas que bailan al ritmo de la cruz."
    )

    # 3. Intentar TTS con ElevenLabs
    audio_path = None
    eleven_success = False
    try:
        voice_id = 'EXAVITQu4vr4xnSDxMaL'  # Voz predeterminada de ElevenLabs (puede ajustarse)
        tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
        headers = {
            'Accept': 'audio/mpeg',
            'Content-Type': 'application/json',
            'xi-api-key': api_key,
        }
        payload = json.dumps({
            'text': poem,
            'model_id': 'eleven_monolingual_v1',
            'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}
        })
        tts_resp = requests.post(tts_url, headers=headers, data=payload, timeout=30)
        if tts_resp.status_code == 200:
            # Guardar audio en archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tmp_file.write(tts_resp.content)
                audio_path = tmp_file.name
            eleven_success = True
        else:
            # Si la respuesta no es 200, consideramos fallback
            eleven_success = False
    except Exception as e:
        eleven_success = False

    # 4. Fallback a gTTS si ElevenLabs falló
    if not eleven_success:
        try:
            tts = gTTS(text=poem, lang='es')  # Usamos español para el poema
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                audio_path = tmp_file.name
        except Exception as e:
            return {'ok': False, 'error': f'Fallo el fallback a gTTS: {e}'}

    # 5. Reproducir audio con playsound
    try:
        if not audio_path or not os.path.isfile(audio_path):
            return {'ok': False, 'error': 'Archivo de audio no encontrado después de la generación.'}
        # Asegurarse de usar ruta absoluta sin comillas extra
        abs_path = os.path.abspath(audio_path)
        playsound(abs_path)
        return {'ok': True, 'audio_path': abs_path, 'fallback_used': not eleven_success}
    except Exception as e:
        return {'ok': False, 'error': 'Error al reproducir el audio.', 'exception': str(e), 'audio_path': audio_path}
