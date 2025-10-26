import os
import json
import requests
import tempfile
import sys

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo convierte a audio y lo reproduce.
    Args:
        args (dict): {
            'api_key': str  # clave de ElevenLabs
        }
    Returns:
        dict: {'ok': True, 'audio_path': str} o {'ok': False, 'error': str, 'exception': str (opcional)}
    """
    api_key = args.get('api_key')
    if not api_key:
        return {'ok': False, 'error': 'API key no provista.'}

    # 1. Poema simple (se podría generar dinámicamente)
    poem = (
        "En la quietud del alba, el sol despierta,\n"
        "Sus rayos acarician la tierra tierna,\n"
        "Susurros de viento cantan una canción,\n"
        "Y el día renace en suave emoción."
    )

    # 2. Verificar clave de ElevenLabs (GET /v1/models)
    headers = {"xi-api-key": api_key}
    try:
        test_resp = requests.get('https://api.elevenlabs.io/v1/models', headers=headers, timeout=10)
        eleven_valid = test_resp.status_code == 200
    except Exception as e:
        eleven_valid = False
        eleven_error_msg = f"Error al validar la API key de ElevenLabs: {e}"
    else:
        if not eleven_valid:
            eleven_error_msg = f"Respuesta inesperada al validar la clave: {test_resp.status_code} {test_resp.text}"

    audio_path = None

    # 3. Intentar generar audio con ElevenLabs si la clave es válida
    if eleven_valid:
        try:
            voice_id = 'EXAVITQu4vr4xnSDxMaL'  # voz predeterminada de ElevenLabs
            tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
            tts_headers = {
                'xi-api-key': api_key,
                'Content-Type': 'application/json'
            }
            tts_payload = {
                'text': poem,
                'model_id': 'eleven_monolingual_v1',
                'voice_settings': {
                    'stability': 0.5,
                    'similarity_boost': 0.75
                }
            }
            resp = requests.post(tts_url, headers=tts_headers, json=tts_payload, timeout=30)
            if resp.status_code == 200:
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                tmp_file.write(resp.content)
                tmp_file.close()
                audio_path = tmp_file.name
            else:
                eleven_error_msg = f"ElevenLabs TTS error {resp.status_code}: {resp.text}"
        except Exception as e:
            eleven_error_msg = f"Excepción al llamar a ElevenLabs TTS: {e}"

    # 4. Fallback a gTTS si ElevenLabs falló
    if audio_path is None:
        try:
            from gtts import gTTS
        except Exception as e:
            return {'ok': False, 'error': 'gTTS no está disponible y ElevenLabs falló.', 'exception': str(e)}
        try:
            tts = gTTS(text=poem, lang='es')
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(tmp_file.name)
            audio_path = tmp_file.name
        except Exception as e:
            return {'ok': False, 'error': 'Error al generar audio con gTTS.', 'exception': str(e)}

    # 5. Reproducir el audio con playsound
    try:
        from playsound import playsound
    except Exception as e:
        return {'ok': False, 'error': 'playsound no está instalado.', 'exception': str(e)}
    try:
        # playsound necesita una ruta absoluta sin comillas
        abs_path = os.path.abspath(audio_path)
        playsound(abs_path)
        return {'ok': True, 'audio_path': abs_path}
    except Exception as e:
        return {'ok': False, 'error': 'Error al reproducir el audio.', 'exception': str(e), 'audio_path': audio_path}
