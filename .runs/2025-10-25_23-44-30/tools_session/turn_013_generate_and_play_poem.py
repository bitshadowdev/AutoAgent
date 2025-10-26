import os
import sys
import subprocess
import json
import io
import requests

# Ensure required packages are installed
def _install(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

for pkg in ['simpleaudio', 'pydub']:
    _install(pkg)

import simpleaudio as sa
from pydub import AudioSegment

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo convierte a audio con ElevenLabs y lo reproduce.
    Args:
        args: {
            'api_key': str  # clave de ElevenLabs
        }
    Returns:
        dict con 'ok': bool y opcionalmente 'error' o 'message'.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'Falta la api_key'}

        # 1️⃣ Poema estático (puede ser personalizado)
        poem = (
            "En la quietud del alba, el verso se despierta,\n"
            "susurra el viento entre sombras inciertas,\n"
            "las luces doradas pintan la tierra,\n"
            "y el corazón late, libre, sin guerra."
        )

        # 2️⃣ Llamada a ElevenLabs (voz por defecto)
        voice_id = 'EXAVITQu4rvGda1gGQ0YIc'  # voz en inglés; cambiar si se desea otro idioma
        url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
        headers = {
            'xi-api-key': api_key,
            'Content-Type': 'application/json',
            'Accept': 'audio/mpeg'
        }
        data = {'text': poem}
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error API ElevenLabs: {response.status_code} {response.text}'}

        # 3️⃣ Guardar MP3 en carpeta temporal
        temp_dir = os.path.join(os.getenv('TEMP') or os.getcwd(), 'elevenlabs')
        os.makedirs(temp_dir, exist_ok=True)
        mp3_path = os.path.join(temp_dir, 'poema.mp3')
        with open(mp3_path, 'wb') as f:
            f.write(response.content)
        if not os.path.exists(mp3_path):
            return {'ok': False, 'error': 'El archivo MP3 no se creó'}

        # 4️⃣ Convertir MP3 a WAV en memoria
        audio_seg = AudioSegment.from_file(mp3_path, format='mp3')
        wav_io = io.BytesIO()
        audio_seg.export(wav_io, format='wav')
        wav_io.seek(0)

        # 5️⃣ Reproducir con simpleaudio
        wave_obj = sa.WaveObject.from_wave_file(wav_io)
        play_obj = wave_obj.play()
        play_obj.wait_done()

        return {'ok': True, 'message': 'Poema reproducido con éxito', 'file': mp3_path}
    except Exception as e:
        return {'ok': False, 'error': str(e)}