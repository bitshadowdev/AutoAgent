import requests
import json
import simpleaudio as sa
import os
from pathlib import Path

def generate_and_play_poem(args: dict) -> dict:
    """Genera y reproduce un poema usando ElevenLabs.
    args debe contener la clave API bajo la llave 'api_key'.
    """
    api_key = args.get('api_key')
    if not api_key or not isinstance(api_key, str):
        return {'ok': False, 'error': 'API key no proporcionada o no es una cadena.'}

    headers = {
        'xi-api-key': api_key.strip()
    }

    # Paso 1: listar voces
    try:
        resp = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers, timeout=10)
        if resp.status_code == 401:
            return {'ok': False, 'error': 'Authorization failed (401). Verifica la API key.'}
        resp.raise_for_status()
        voices_data = resp.json()
        voices = voices_data.get('voices', [])
        if not voices:
            return {'ok': False, 'error': 'No se encontraron voces en la cuenta ElevenLabs.'}
        voice_id = voices[0].get('voice_id')
        if not voice_id:
            return {'ok': False, 'error': 'La respuesta de voces no contiene "voice_id".'}
    except requests.RequestException as e:
        return {'ok': False, 'error': f'Error al listar voces: {str(e)}'}
    except (ValueError, json.JSONDecodeError):
        return {'ok': False, 'error': 'Respuesta inválida al listar voces.'}

    # Paso 2: generar poema
    poem_text = (
        "En la quietud de la noche, susurra el viento,\n"
        "Lleva recuerdos de lunas lejanas,\n"
        "Estrellas que pintan sueños en el cielo,\n"
        "Y el corazón late, vibrante y sereno."
    )
    tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream'
    tts_headers = {
        'xi-api-key': api_key.strip(),
        'Accept': 'audio/wav',
        'Content-Type': 'application/json'
    }
    tts_payload = {
        'text': poem_text,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {}
    }
    try:
        tts_resp = requests.post(tts_url, headers=tts_headers, json=tts_payload, timeout=30)
        if tts_resp.status_code == 401:
            return {'ok': False, 'error': 'Authorization failed (401) al generar audio. Verifica la API key.'}
        if tts_resp.status_code == 404:
            return {'ok': False, 'error': 'Voice not found (404). Intentando con otra voz si estuviera disponible.'}
        tts_resp.raise_for_status()
        audio_bytes = tts_resp.content
    except requests.RequestException as e:
        return {'ok': False, 'error': f'Error al generar audio: {str(e)}'}

    # Paso 3: guardar archivo WAV
    output_path = Path('poem.wav')
    try:
        with open(output_path, 'wb') as f:
            f.write(audio_bytes)
    except OSError as e:
        return {'ok': False, 'error': f'Error al escribir el archivo WAV: {str(e)}'}

    # Paso 4: reproducir audio
    try:
        wave_obj = sa.WaveObject.from_wave_file(str(output_path))
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        return {'ok': False, 'error': f'Error al reproducir el audio: {str(e)}'}

    return {'ok': True, 'message': 'Poema reproducido exitosamente.', 'audio_file': str(output_path)}