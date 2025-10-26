import os
import sys
import subprocess
import requests
import io
import simpleaudio as sa
from pydub import AudioSegment
import tempfile

def generate_and_play_poem_v3(args: dict) -> dict:
    """Genera un poema, lo convierte a audio con ElevenLabs y lo reproduce.
    args debe contener la clave 'api_key' con la API key de ElevenLabs.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'Falta la api_key'}

        # 1) Poema simple
        poem = (
            "En la quietud del alba, susurra el viento,\n"
            "pintando de oro el sueño del tiempo.\n"
            "Las hojas bailan, historias al pasar,\n"
            "y el corazón late al compás del mar."
        )

        # 2) Llamada a ElevenLabs
        voice_id = "EXAVITQu4vr4xnSDxMaL"  # voz predeterminada de ejemplo
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json"
        }
        payload = {
            "text": poem,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error API ElevenLabs: {response.status_code} {response.text}'}
        mp3_bytes = response.content

        # 3) Guardar MP3 en carpeta temporal
        temp_dir = os.path.join(tempfile.gettempdir(), "elevenlabs")
        os.makedirs(temp_dir, exist_ok=True)
        mp3_path = os.path.join(temp_dir, "poema.mp3")
        with open(mp3_path, "wb") as f:
            f.write(mp3_bytes)
        if not os.path.exists(mp3_path):
            return {'ok': False, 'error': 'El archivo MP3 no se guardó correctamente'}

        # 4) Convertir MP3 a WAV en memoria y reproducir con simpleaudio
        audio = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
        raw_data = audio.raw_data
        sample_rate = audio.frame_rate
        num_channels = audio.channels
        bytes_per_sample = audio.sample_width
        play_obj = sa.play_buffer(raw_data, num_channels, bytes_per_sample, sample_rate)
        play_obj.wait_done()

        return {'ok': True, 'file': mp3_path, 'poem': poem}
    except Exception as e:
        return {'ok': False, 'error': str(e)}