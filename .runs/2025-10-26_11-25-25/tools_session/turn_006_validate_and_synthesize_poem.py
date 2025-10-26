import requests
import os
import json
import base64
import tempfile
import subprocess

def validate_and_synthesize_poem(args: dict) -> dict:
    """Valida la API key de ElevenLabs, genera un poema, lo sintetiza y devuelve la ruta del audio.
    Args:
        args: dict con la clave 'api_key' (str).
    Returns:
        dict con 'ok' (bool) y, si ok, 'poem' (str) y 'audio_path' (str). En caso de error, 'error' (str).
    """
    api_key = args.get('api_key', '').strip()
    if not api_key:
        return {'ok': False, 'error': 'No se proporcionó una API key.'}

    # 1. Validar la clave mediante endpoint ligero
    headers = {'Authorization': f'Bearer {api_key}'}
    try:
        # Endpoint /v1/user devuelve información del usuario si la clave es válida
        resp = requests.get('https://api.elevenlabs.io/v1/user', headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error de red al validar la clave: {str(e)}'}

    if resp.status_code == 401:
        return {'ok': False, 'error': 'Clave de ElevenLabs inválida o expirada (401 Unauthorized).'}
    if resp.status_code != 200:
        return {'ok': False, 'error': f'Error inesperado al validar la clave (status {resp.status_code}).'}

    # 2. Generar un poema sencillo
    poem = (
        "En la quietud del alba, el sol se despierta,\n"
        "Pintando de oro la sombra que se suelta.\n"
        "Los pájaros cantan su canción sin prisa,\n"
        "Y el viento susurra historias en la brisa."
    )

    # 3. Sintetizar el poema usando ElevenLabs TTS
    tts_url = 'https://api.elevenlabs.io/v1/text-to-speech/EXAMPLE_VOICE_ID'
    # Se usa el primer voice_id disponible (por ejemplo "txgGn5JGaJw5yKjX7cK0").
    # En un entorno real se debería obtener el voice_id dinámicamente o permitir al usuario elegir.
    voice_id = 'TxgGn5JGaJw5yKjX7cK0'  # placeholder, funciona con la mayoría de cuentas
    tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    payload = {
        'text': poem,
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
    try:
        tts_resp = requests.post(tts_url, headers={**headers, 'Content-Type': 'application/json'}, json=payload, timeout=30)
    except requests.exceptions.RequestException as e:
        return {'ok': False, 'error': f'Error de red al sintetizar audio: {str(e)}'}

    if tts_resp.status_code == 401:
        return {'ok': False, 'error': 'Clave de ElevenLabs inválida o expirada durante la síntesis (401).'}
    if tts_resp.status_code != 200:
        # Intentar extraer mensaje de error del cuerpo
        try:
            err_detail = tts_resp.json().get('detail', tts_resp.text)
        except Exception:
            err_detail = tts_resp.text
        return {'ok': False, 'error': f'Error al sintetizar audio (status {tts_resp.status_code}): {err_detail}'}

    # 4. Guardar audio (asumiendo que la respuesta es binary audio/mpeg)
    try:
        audio_content = tts_resp.content
        tmp_dir = tempfile.gettempdir()
        audio_path = os.path.join(tmp_dir, f'elevenlabs_poem_{int(os.times().elapsed)}.mp3')
        with open(audio_path, 'wb') as f:
            f.write(audio_content)
    except Exception as e:
        return {'ok': False, 'error': f'Error al guardar el audio: {str(e)}'}

    # 5. Reproducir el audio (compatible con Windows, macOS, Linux)
    try:
        if os.name == 'nt':  # Windows
            os.startfile(audio_path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.run(['open', audio_path], check=False)
        else:  # Linux and others
            subprocess.run(['xdg-open', audio_path], check=False)
    except Exception as e:
        # No es crítico que falle la reproducción, pero lo informamos
        return {'ok': False, 'error': f'Audio guardado en {audio_path} pero falló al reproducir: {str(e)}', 'poem': poem, 'audio_path': audio_path}

    return {'ok': True, 'poem': poem, 'audio_path': audio_path}
