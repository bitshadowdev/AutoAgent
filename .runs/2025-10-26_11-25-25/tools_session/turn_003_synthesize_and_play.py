import os
import json
import requests
import tempfile
import subprocess
from pathlib import Path

def synthesize_and_play(args: dict) -> dict:
    """Genera un poema, lo sintetiza con ElevenLabs y guarda el audio.
    Parámetros esperados en *args*:
        - api_key (str): clave de API de ElevenLabs.
    Devuelve dict con:
        - ok (bool)
        - poem (str) (si ok)
        - audio_path (str) (ruta al archivo mp3, si ok)
        - error (str) (si no ok)
    """
    api_key = args.get('api_key', '').strip()
    if not api_key:
        return {'ok': False, 'error': 'API key missing.'}
    if not api_key.startswith('sk_'):
        return {'ok': False, 'error': 'API key does not appear to be a valid ElevenLabs key (must start with "sk_").'}

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    # Paso 1: verificación previa de la clave (lista de voces)
    try:
        test_resp = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers, timeout=10)
    except requests.RequestException as e:
        return {'ok': False, 'error': f'Network error during key validation: {str(e)}'}
    if test_resp.status_code == 401:
        return {'ok': False, 'error': 'Invalid or expired ElevenLabs API key (401 Unauthorized).'}
    if not test_resp.ok:
        return {'ok': False, 'error': f'Error during key validation: {test_resp.status_code} {test_resp.text}'}

    # Paso 2: generar poema
    poem = (
        "En la bruma del alba, susurros del viento,\n"
        "Pintan en el cielo un lienzo de silencio,\n"
        "Las estrellas descienden, guardas del tiempo,\n"
        "Y el corazón late, libre, sin retroceso."
    )

    # Seleccionar una voz por defecto (puede cambiarse si se desea)
    voice_id = 'EXAVITQu4vr4xnSDxMaL'  # voz "Rachel"
    tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    payload = {
        'text': poem,
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
    try:
        resp = requests.post(tts_url, headers=headers, json=payload, timeout=20)
    except requests.RequestException as e:
        return {'ok': False, 'error': f'Network error during synthesis: {str(e)}'}
    if resp.status_code == 401:
        return {'ok': False, 'error': 'Invalid or expired ElevenLabs API key during synthesis (401 Unauthorized).'}
    if not resp.ok:
        return {'ok': False, 'error': f'ElevenLabs API error: {resp.status_code} {resp.text}'}

    # Guardar audio en archivo temporal
    try:
        tmp_dir = Path(tempfile.gettempdir())
        audio_path = tmp_dir / f'elevenlabs_poem_{int(os.getpid())}.mp3'
        with open(audio_path, 'wb') as f:
            f.write(resp.content)
    except Exception as e:
        return {'ok': False, 'error': f'Failed to write audio file: {str(e)}'}

    # Intentar reproducir el audio (si hay un reproductor disponible)
    try:
        # Usamos ffplay si está disponible, de lo contrario omitimos la reproducción.
        subprocess.run(['ffplay', '-nodisp', '-autoexit', str(audio_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception:
        # Silenciosamente ignoramos errores de reproducción; la ruta del archivo se devuelve de todas formas.
        pass

    return {'ok': True, 'poem': poem, 'audio_path': str(audio_path)}