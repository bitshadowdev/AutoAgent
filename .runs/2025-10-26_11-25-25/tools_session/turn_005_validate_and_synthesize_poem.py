import os
import json
import base64
import tempfile
import subprocess
import requests

def validate_and_synthesize_poem(args: dict) -> dict:
    """Valida la API key de ElevenLabs, genera un poema, lo sintetiza y guarda el audio.
    Retorna {'ok': True, 'audio_path': <ruta>} si todo sale bien.
    Si la clave es inválida devuelve {'ok': False, 'error': <mensaje>}.
    """
    api_key = args.get('api_key', '').strip()
    if not api_key:
        return {'ok': False, 'error': 'No se proporcionó una API key.'}
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    # 1. Validar la clave con una petición ligera
    try:
        validate_resp = requests.get('https://api.elevenlabs.io/v1/user', headers=headers, timeout=10)
    except requests.RequestException as e:
        return {'ok': False, 'error': f'Error de red al validar la clave: {str(e)}'}
    if validate_resp.status_code == 401:
        return {'ok': False, 'error': 'Clave de ElevenLabs inválida o expirada (401). Por favor, proporciona una clave válida.'}
    if not validate_resp.ok:
        return {'ok': False, 'error': f'Error al validar la clave: HTTP {validate_resp.status_code}'}

    # 2. Generar poema (texto fijo)
    poem = (
        "En la quietud del alba, el silencio susurra,\n"
        "las sombras se disipan, la luz se inaugura.\n"
        "Cada hoja reposada lleva un sueño,\n"
        "y el viento, poeta, escribe su empeño.\n"
    )

    # 3. Sintetizar con ElevenLabs
    voice_id = 'EXAVITQu4vr4xnGO'  # voz predeterminada de ejemplo
    tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    payload = {
        'text': poem,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
    try:
        tts_resp = requests.post(tts_url, headers=headers, json=payload, timeout=20)
    except requests.RequestException as e:
        return {'ok': False, 'error': f'Error de red al sintetizar el texto: {str(e)}'}

    if tts_resp.status_code == 401:
        return {'ok': False, 'error': 'Clave de ElevenLabs inválida o expirada durante la síntesis (401).'}
    if not tts_resp.ok:
        # Intentar extraer mensaje de error
        try:
            err_json = tts_resp.json()
            detail = err_json.get('detail', tts_resp.text)
        except Exception:
            detail = tts_resp.text
        return {'ok': False, 'error': f'Error al sintetizar: HTTP {tts_resp.status_code} - {detail}'}

    # 4. Guardar audio a archivo temporal
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tmp_file.write(tts_resp.content)
            audio_path = tmp_file.name
    except Exception as e:
        return {'ok': False, 'error': f'No se pudo guardar el audio: {str(e)}'}

    # 5. Reproducir (intenta usar reprodución del sistema)
    try:
        # macOS: afplay, Linux: mpg123 o ffplay, Windows: PowerShell
        if os.name == 'nt':
            # Windows: usar PowerShell para reproducir
            subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{audio_path}").PlaySync();'], check=False)
        else:
            # Intentar afplay o mpg123
            if shutil.which('afplay'):
                subprocess.run(['afplay', audio_path], check=False)
            elif shutil.which('mpg123'):
                subprocess.run(['mpg123', audio_path], check=False)
            elif shutil.which('ffplay'):
                subprocess.run(['ffplay', '-autoexit', '-nodisp', audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception:
        # Si falla la reproducción, solo devolvemos la ruta
        pass

    return {'ok': True, 'audio_path': audio_path, 'poem': poem}
