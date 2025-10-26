import os
import sys
import subprocess
import json
import requests
import io
import simpleaudio as sa
from pydub import AudioSegment

# Asegurar dependencias
try:
    import requests
    import simpleaudio
    from pydub import AudioSegment
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', 'requests', 'simpleaudio', 'pydub'])
    import requests
    import simpleaudio as sa
    from pydub import AudioSegment

def generate_and_play_poem_v2(args: dict) -> dict:
    """Genera un poema, lo convierte a audio con ElevenLabs y lo reproduce.
    Args:
        args (dict): debe contener la clave 'api_key'.
    Returns:
        dict: {'ok': True, 'mp3': <ruta>, 'wav': <ruta>} o {'ok': False, 'error': <msg>}
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'Falta la api_key'}

        # 1. Poema estático (puedes reemplazar por generación dinámica)
        poem = (
            "En la quietud del alba, el sol susurra,\n"
            "Los pájaros cantan, la brisa murmura,\n"
            "Cada hoja danza bajo su luz dorada,\n"
            "Y el mundo despierta, en calma abrazada."
        )

        # 2. Llamada a ElevenLabs TTS
        voice_id = "EXAVITQu4vr4xnSDxMaL"  # voz predeterminada
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}" 
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": poem,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error en ElevenLabs: {response.status_code} {response.text}'}

        # 3. Guardar MP3 en carpeta temporal
        temp_dir = os.path.join(os.getenv('TEMP') or '/tmp', 'elevenlabs_audio')
        os.makedirs(temp_dir, exist_ok=True)
        mp3_path = os.path.join(temp_dir, 'poem.mp3')
        with open(mp3_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        if not os.path.exists(mp3_path):
            return {'ok': False, 'error': 'El archivo MP3 no se guardó correctamente.'}

        # 4. Convertir MP3 a WAV (pydub)
        audio = AudioSegment.from_file(mp3_path, format='mp3')
        wav_path = os.path.join(temp_dir, 'poem.wav')
        audio.export(wav_path, format='wav')
        if not os.path.exists(wav_path):
            return {'ok': False, 'error': 'La conversión a WAV falló.'}

        # 5. Reproducir WAV con simpleaudio
        wave_obj = sa.WaveObject.from_wave_file(wav_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()

        return {'ok': True, 'mp3': mp3_path, 'wav': wav_path, 'poem': poem}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
