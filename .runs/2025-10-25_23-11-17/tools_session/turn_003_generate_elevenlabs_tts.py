import os
import json
import base64
import requests

def generate_elevenlabs_tts(args: dict) -> dict:
    try:
        api_key = args.get('api_key')
        text = args.get('text')
        voice_id = args.get('voice_id', '21m00Tcm4TlvDq8ikWZ')  # voice default
        if not api_key or not text:
            return {'ok': False, 'error': 'Missing api_key or text'}
        url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
        headers = {
            'xi-api-key': api_key,
            'Content-Type': 'application/json'
        }
        data = {
            'text': text,
            'model_id': 'eleven_monolingual_v1',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.75
            }
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            return {'ok': False, 'error': f'API error {response.status_code}: {response.text}'}
        audio_bytes = response.content
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        return {'ok': True, 'audio_base64': audio_b64}
    except Exception as e:
        return {'ok': False, 'error': str(e)}