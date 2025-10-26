import requests
import base64

def generate_tts(args: dict) -> dict:
    """
    Llama a la API de ElevenLabs para generar voz a partir de texto.
    Parámetros esperados en `args`:
        - api_key (str): clave de API de ElevenLabs.
        - text (str): texto que se convertirá a voz.
        - voice_id (str, opcional): id de la voz a usar. Por defecto usa una voz pública.
    Retorna dict con:
        - ok (bool): True si se obtuvo el audio.
        - audio_base64 (str): audio en formato base64 (WAV).
        - error (str, opcional): mensaje de error si ocurre.
    """
    api_key = args.get('api_key')
    text = args.get('text')
    voice_id = args.get('voice_id', 'EXAVITQu4vr4xnSDxMaL')  # voz pública de ejemplo
    if not api_key or not text:
        return {'ok': False, 'error': 'Faltan api_key o text'}
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream'
    headers = {
        'xi-api-key': api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        'text': text,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code != 200:
            return {'ok': False, 'error': f'API error {response.status_code}: {response.text}'}
        audio_bytes = response.content
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        return {'ok': True, 'audio_base64': audio_b64}
    except Exception as e:
        return {'ok': False, 'error': str(e)}