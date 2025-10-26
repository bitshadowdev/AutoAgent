import requests
import json
import os
import tempfile
from pathlib import Path
from playsound import playsound

def validate_and_synthesize_poem(args: dict) -> dict:
    """Valida la API key de ElevenLabs, genera un poema y lo reproduce.
    Args:
        args: {'api_key': str}
    Returns:
        dict con {'ok': bool, 'message': str, 'audio_path': str (opcional)}
    """
    api_key = str(args.get('api_key', '')).strip()
    if not api_key:
        return {'ok': False, 'error': 'No se proporcionó ninguna API key.'}

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }

    # 1. Validar la clave con una petición ligera
    try:
        validate_resp = requests.get('https://api.elevenlabs.io/v1/user', headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error de red al validar la clave: {e}'}

    if validate_resp.status_code == 401:
        return {'ok': False, 'error': 'Clave de ElevenLabs inválida o expirada (401 Unauthorized). Por favor, proporciona una clave válida.'}
    if not validate_resp.ok:
        return {'ok': False, 'error': f'Error inesperado al validar la clave: HTTP {validate_resp.status_code}'}

    # 2. Generar un poema simple
    poema = (
        "En la quietud del alba, murmura el viento,\n"
        "Pintando sombras de plata sobre el firmamento.\n"
        "Los sueños despiertan, ligeros como albor,\n"
        "Y la vida susurra su eterno amor."
    )

    # 3. Sintetizar vía ElevenLabs
    # Usaremos el voice_id predeterminado (puedes cambiarlo si lo deseas)
    voice_id = 'EXAVITQu4vr4xnSDxMaL'
    tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    payload = {
        'text': poema,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
    tts_headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg'
    }
    try:
        tts_resp = requests.post(tts_url, headers=tts_headers, data=json.dumps(payload), timeout=30)
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error de red al sintetizar el texto: {e}'}

    if tts_resp.status_code == 401:
        return {'ok': False, 'error': 'Clave de ElevenLabs inválida o expirada durante la síntesis (401).'}
    if not tts_resp.ok:
        # Intentamos extraer mensaje de error JSON si está disponible
        try:
            err_json = tts_resp.json()
            err_msg = err_json.get('detail', tts_resp.text)
        except Exception:
            err_msg = tts_resp.text
        return {'ok': False, 'error': f'Error al sintetizar el audio: HTTP {tts_resp.status_code} - {err_msg}'}

    # 4. Guardar audio a archivo temporal
    try:
        tmp_dir = Path(tempfile.gettempdir())
        audio_path = tmp_dir / f'poema_{os.urandom(4).hex()}.mp3'
        with open(audio_path, 'wb') as f:
            f.write(tts_resp.content)
    except Exception as e:
        return {'ok': False, 'error': f'Error al guardar el audio: {e}'}

    # 5. Reproducir audio
    try:
        playsound(str(audio_path))
    except Exception as e:
        return {'ok': False, 'error': f'Error al reproducir el audio: {e}', 'audio_path': str(audio_path)}

    return {
        'ok': True,
        'message': 'Poema generado y reproducido exitosamente.',
        'audio_path': str(audio_path)
    }
