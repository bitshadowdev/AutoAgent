import requests
import json
import os
import base64
import random
import string
from pathlib import Path

def elevenlabs_poem(args: dict) -> dict:
    """Genera un poema sencillo, lo envía a ElevenLabs para sintetizar audio y devuelve el texto y, si es posible, la ruta al archivo de audio.
    Maneja errores de la API y, en caso de fallo, retorna solo el poema.
    La clave API no se expone en la salida.
    """
    # Configuración básica
    api_key = args.get('api_key')
    if not api_key:
        return {'ok': False, 'error': 'No se proporcionó la clave API de ElevenLabs.'}

    # Generador de poema simple (puedes personalizar)
    def generar_poema():
        versos = [
            "En la quietud de la noche, la luna susurra,",
            "Los sueños navegan en mares de plata.",
            "El viento acaricia recuerdos perdidos,",
            "Y el alba despierta esperanzas renovadas."
        ]
        random.shuffle(versos)
        return "\n".join(versos)

    poema = generar_poema()

    # Parámetros de ElevenLabs (voice_id predeterminado)
    voice_id = 'EXAVITQu4vr4xnSDxMaL'  # voz por defecto, puede cambiarse
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    headers = {
        'Accept': 'audio/mpeg',
        'Content-Type': 'application/json',
        'xi-api-key': api_key
    }
    payload = {
        'text': poema,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            # Guardamos el audio en un archivo temporal
            audio_dir = Path('elevenlabs_audio')
            audio_dir.mkdir(parents=True, exist_ok=True)
            # Nombre de archivo aleatorio para evitar colisiones
            random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=12)) + '.mp3'
            audio_path = audio_dir / random_name
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            return {
                'ok': True,
                'poem': poema,
                'audio_path': str(audio_path),
                'message': 'Audio generado exitosamente.'
            }
        else:
            # Si la API responde con error, devolvemos solo el poema con mensaje de aviso
            error_detail = ''
            try:
                err_json = response.json()
                error_detail = err_json.get('detail', response.text)
            except Exception:
                error_detail = response.text
            return {
                'ok': False,
                'error': f'Error de ElevenLabs ({response.status_code}): {error_detail}',
                'poem': poema,
                'audio_path': None,
                'message': 'No se pudo generar audio; se devuelve solo el texto.'
            }
    except requests.exceptions.RequestException as e:
        # Capturamos cualquier excepción de red o timeout
        return {
            'ok': False,
            'error': f'Excepción al contactar ElevenLabs: {str(e)}',
            'poem': poema,
            'audio_path': None,
            'message': 'No se pudo generar audio; se devuelve solo el texto.'
        }
