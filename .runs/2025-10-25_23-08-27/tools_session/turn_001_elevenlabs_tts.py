import requests
import base64

def elevenlabs_tts(args: dict) -> dict:
    """Genera audio con ElevenLabs a partir de texto.
    Args:
        args: dict con claves:
            - api_key: str, clave de API de ElevenLabs.
            - text: str, texto a convertir en habla.
            - voice_id: str, opcional, id de la voz a usar; por defecto usa la voz "EXAVITQu4vr4xnSDxMaL" (uno de los modelos estándar).
            - model_id: str, opcional, modelo de TTS; por defecto "eleven_monolingual_v1".
    Returns:
        dict con:
            - ok: bool
            - audio_base64: str (si ok) o None
            - error: str (si no ok)
    """
    api_key = args.get('api_key')
    text = args.get('text')
    voice_id = args.get('voice_id', 'EXAVITQu4vr4xnSDxMaL')
    model_id = args.get('model_id', 'eleven_monolingual_v1')

    if not api_key or not text:
        return {'ok': False, 'audio_base64': None, 'error': 'api_key y text son requeridos'}

    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    headers = {
        'xi-api-key': api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        'text': text,
        'model_id': model_id,
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code != 200:
            return {'ok': False, 'audio_base64': None, 'error': f'Error HTTP {response.status_code}: {response.text}'}
        # La respuesta es audio en formato mp3
        audio_bytes = response.content
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        return {'ok': True, 'audio_base64': audio_b64, 'error': None}
    except Exception as e:
        return {'ok': False, 'audio_base64': None, 'error': str(e)}