import os
import json
import requests
import tempfile
import base64
from pathlib import Path

def synthesize_and_play(args: dict) -> dict:
    """Synthesizes a hard‑coded poem with ElevenLabs and saves the audio.

    Args:
        args: dict with key 'api_key' (str). Optional 'voice_id' (str).

    Returns:
        dict with:
            - ok (bool): True if synthesis succeeded.
            - audio_path (str, optional): Path to the saved WAV file.
            - audio_base64 (str, optional): Base64 string of the audio (fallback for environments without file access).
            - error (str, optional): Error message when ok is False.
    """
    api_key = args.get('api_key')
    if not api_key:
        return {'ok': False, 'error': 'Missing API key.'}

    # Simple validation request: list all available voices (GET) – returns 401 if key invalid.
    headers = {'Authorization': f'Bearer {api_key}', 'Accept': 'application/json'}
    try:
        test_resp = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers, timeout=10)
    except requests.RequestException as e:
        return {'ok': False, 'error': f'Network error during API key validation: {str(e)}'}

    if test_resp.status_code == 401:
        return {'ok': False, 'error': 'Invalid or expired ElevenLabs API key (401 Unauthorized).'}
    if not test_resp.ok:
        return {'ok': False, 'error': f'Unexpected response during key validation: {test_resp.status_code} {test_resp.text}'}

    # Poema a sintetizar.
    poema = (
        "En la quietud del alba, susurra el viento,\n"
        "Pintando de oro la tierra escarlata.\n"
        "Cada hoja, un verso que el tiempo llevó,\n"
        "Y el sol escribe sueños en la madrugada."
    )

    voice_id = args.get('voice_id', 'EXAVITQu4vr4xnSDxMaL')  # voz predeterminada de ElevenLabs
    synth_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream'
    payload = {
        'text': poema,
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
    headers.update({
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg'
    })

    try:
        resp = requests.post(synth_url, headers=headers, json=payload, timeout=30)
    except requests.RequestException as e:
        return {'ok': False, 'error': f'Network error during synthesis: {str(e)}'}

    if resp.status_code == 401:
        return {'ok': False, 'error': 'Invalid or expired ElevenLabs API key during synthesis (401 Unauthorized).'}
    if not resp.ok:
        # Intentamos extraer mensaje de error JSON si está disponible
        try:
            err_detail = resp.json()
            err_msg = json.dumps(err_detail)
        except Exception:
            err_msg = resp.text
        return {'ok': False, 'error': f'API error {resp.status_code}: {err_msg}'}

    # Guardamos audio en archivo temporal
    try:
        # ElevenLabs devuelve MP3; lo guardamos tal cual.
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tmp_file.write(resp.content)
            audio_path = tmp_file.name
        # Además, devolvemos base64 por seguridad del entorno.
        audio_b64 = base64.b64encode(resp.content).decode('utf-8')
        return {'ok': True, 'audio_path': audio_path, 'audio_base64': audio_b64}
    except Exception as e:
        return {'ok': False, 'error': f'Error saving audio file: {str(e)}'}