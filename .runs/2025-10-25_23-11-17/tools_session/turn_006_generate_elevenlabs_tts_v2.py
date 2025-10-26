import os
import base64
import requests

def generate_elevenlabs_tts_v2(args: dict) -> dict:
    """Genera audio con ElevenLabs y devuelve el audio en base64.
    Args:
        args: dict con claves:
            - api_key (str): clave de API de ElevenLabs.
            - text (str): texto a sintetizar.
            - voice_id (str, opcional): id de la voz a usar. Se usa una voz por defecto si no se indica.
    Returns:
        dict con:
            - ok (bool): True si la llamada fue exitosa.
            - audio_base64 (str, opcional): cadena base64 del MP3.
            - error (str, opcional): mensaje de error en caso de falla.
    """
    api_key = args.get('api_key')
    text = args.get('text')
    voice_id = args.get('voice_id', 'EXAVITQu4vr4xnSd9NK6')  # voice de ejemplo válida
    if not api_key or not text:
        return {'ok': False, 'error': 'Faltan api_key o text.'}
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream'
    headers = {
        'Accept': 'audio/mpeg',
        'xi-api-key': api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        'text': text,
        'model_id': 'eleven_multilingual_v2',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
    except Exception as e:
        return {'ok': False, 'error': f'Excepción al conectar con la API: {str(e)}'}
    if response.status_code != 200:
        # Intentar extraer mensaje de error JSON
        try:
            err_json = response.json()
            err_msg = err_json.get('detail', err_json)
        except Exception:
            err_msg = response.text
        return {'ok': False, 'error': f'API error {response.status_code}: {err_msg}'}
    # Convertir audio binario a base64
    audio_b64 = base64.b64encode(response.content).decode('utf-8')
    return {'ok': True, 'audio_base64': audio_b64}
