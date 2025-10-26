import os
import json
import requests
import tempfile
import uuid
import io
import simpleaudio as sa
from pydub import AudioSegment

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo envía a ElevenLabs TTS, lo guarda como MP3 en la carpeta temporal,
    lo convierte a WAV y lo reproduce con simpleaudio.
    Args:
        args: dict con la clave 'api_key' (string).
    Returns:
        dict con 'ok': bool y 'file': ruta al archivo WAV reproducido o 'error' en caso de falla.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'api_key no provisto'}

        # 1. Poema estático (puede sustituirse por generación dinámica)
        poem = (
            "En la sombra del tiempo, susurra el viento,\n"
            "Lleva recuerdos de un sueño eterno,\n"
            "Estrellas pintan el cielo de plata,\n"
            "Y el alba renace, luz que desata."
        )

        # 2. Preparar carpeta temporal
        temp_dir = tempfile.gettempdir()
        os.makedirs(temp_dir, exist_ok=True)

        # 3. Parámetros de ElevenLabs (usar voz por defecto)
        voice_id = "EXAVITQu4vr4xnSDxMaL"  # voz en inglés, cambiar si se desea
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        payload = {
            "text": poem,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload), stream=True, timeout=30)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error de la API ElevenLabs: {response.status_code} {response.text}'}

        # 4. Guardar MP3
        mp3_filename = os.path.join(temp_dir, f"poema_{uuid.uuid4().hex}.mp3")
        with open(mp3_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        if not os.path.exists(mp3_filename):
            return {'ok': False, 'error': f'No se pudo crear el archivo MP3 en {mp3_filename}'}

        # 5. Convertir MP3 a WAV en memoria y guardarlo
        audio = AudioSegment.from_file(mp3_filename, format="mp3")
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)
        wav_filename = os.path.join(temp_dir, f"poema_{uuid.uuid4().hex}.wav")
        with open(wav_filename, 'wb') as f:
            f.write(wav_io.read())

        if not os.path.exists(wav_filename):
            return {'ok': False, 'error': f'No se pudo crear el archivo WAV en {wav_filename}'}

        # 6. Reproducir WAV con simpleaudio
        wave_obj = sa.WaveObject.from_wave_file(wav_filename)
        play_obj = wave_obj.play()
        play_obj.wait_done()

        return {'ok': True, 'file': wav_filename}
    except Exception as e:
        return {'ok': False, 'error': str(e)}