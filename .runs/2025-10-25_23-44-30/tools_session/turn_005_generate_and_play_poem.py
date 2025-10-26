import os
import json
import requests
import tempfile
import io
import subprocess

# Intentar instalar dependencias si faltan
def _ensure_package(pkg_name):
    try:
        __import__(pkg_name)
    except ImportError:
        subprocess.check_call(['python', '-m', 'pip', 'install', pkg_name])

_ensure_package('simpleaudio')
_ensure_package('pydub')

import simpleaudio as sa
from pydub import AudioSegment

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo envía a ElevenLabs TTS, guarda y reproduce el audio.
    Args:
        args: {'api_key': '<tu_api_key>'}
    Returns:
        dict con 'ok': bool y opcionalmente 'error' o 'message'.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'Falta la api_key en los argumentos.'}

        # 1️⃣ Poema estático (puedes reemplazar por generación dinámica)
        poema = (
            "En la quietud de la noche, la luna susurra,\n"
            "las estrellas cantan un viejo verso,\n"
            "y el viento, suave, lleva al recuerdo\n"
            "el eco de un sueño inmenso."
        )

        # 2️⃣ Parámetros de ElevenLabs
        voice_id = "EXAVITQu4vr4xnSDxMaL"  # Voice de ejemplo (puedes cambiarla)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}" \
              "?optimize_streaming_latency=0"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        }
        payload = {
            "text": poema,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }

        # 3️⃣ Llamada a la API
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if response.status_code != 200:
            return {
                'ok': False,
                'error': f"Error de ElevenLabs: {response.status_code} {response.text}"
            }
        mp3_bytes = response.content

        # 4️⃣ Guardar MP3 en carpeta temporal para depuración (opcional)
        temp_dir = tempfile.gettempdir()
        mp3_path = os.path.join(temp_dir, "poema.mp3")
        try:
            with open(mp3_path, "wb") as f:
                f.write(mp3_bytes)
        except OSError as e:
            return {'ok': False, 'error': f"No se pudo escribir el archivo MP3: {e}"}
        if not os.path.exists(mp3_path):
            return {'ok': False, 'error': f"El archivo MP3 no se creó en {mp3_path}."}

        # 5️⃣ Convertir MP3 a WAV en memoria usando pydub
        audio_seg = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
        raw_data = audio_seg.raw_data
        sample_rate = audio_seg.frame_rate
        sample_width = audio_seg.sample_width
        channels = audio_seg.channels

        # 6️⃣ Reproducir con simpleaudio
        try:
            play_obj = sa.play_buffer(raw_data, num_channels=channels,
                                      bytes_per_sample=sample_width,
                                      sample_rate=sample_rate)
            play_obj.wait_done()
        except Exception as e:
            return {'ok': False, 'error': f"Error al reproducir audio: {e}"}

        return {'ok': True, 'message': 'Poema generado y reproducido exitosamente.', 'file': mp3_path}
    except Exception as exc:
        return {'ok': False, 'error': str(exc)}