import requests
import base64

def synthesize_elevenlabs(args: dict) -> dict:
    """Llama a la API de ElevenLabs para generar audio a partir de texto.
    Args:
        args: dict con claves 'api_key' (str) y 'text' (str).
    Returns:
        dict con {'ok': bool, 'audio_base64': str (si ok) o 'error': str}
    """
    api_key = args.get('api_key')
    text = args.get('text', '')
    if not api_key:
        return {'ok': False, 'error': 'Falta la api_key'}
    if not text:
        return {'ok': False, 'error': 'Falta el texto a sintetizar'}
    # Voice ID predeterminado (puede ser cualquiera válido)
    voice_id = 'EXAVITQu4vr4xnSDxMaL'
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream'
    headers = {
        'xi-api-key': api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        'text': text,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {}
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