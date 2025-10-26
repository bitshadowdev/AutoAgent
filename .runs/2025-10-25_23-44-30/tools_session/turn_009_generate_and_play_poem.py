import os
import requests
import io
import simpleaudio as sa
from pydub import AudioSegment

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo envía a ElevenLabs para TTS y lo reproduce.
    Args:
        args: dict con la clave 'api_key' (String).
    Returns:
        dict con 'ok': bool y opcionalmente 'error' o 'message'.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'Falta la api_key'}

        # 1️⃣ Poema simple
        poem = (
            "En la aurora el silencio canta,\n"
            "Luz dorada que al cielo levanta,\n"
            "Sueños vagan en bruma ligera,\n"
            "Y el mundo despierta sin frontera."
        )

        # 2️⃣ Llamada a ElevenLabs (voz por defecto)
        voice_id = "21m00Tcm4TlvDq8ikWAM"  # voz en inglés, funciona para texto genérico
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        }
        payload = {
            "text": poem,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error API ElevenLabs: {response.status_code} {response.text}'}
        mp3_bytes = response.content

        # 3️⃣ Convertir MP3 a WAV en memoria usando pydub
        audio_seg = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
        wav_io = io.BytesIO()
        audio_seg.export(wav_io, format="wav")
        wav_data = wav_io.getvalue()
        wav_io.seek(0)

        # 4️⃣ Reproducir con simpleaudio (play_buffer)
        # Obtener parámetros necesarios
        raw_data = audio_seg.raw_data
        num_channels = audio_seg.channels
        bytes_per_sample = audio_seg.sample_width
        sample_rate = audio_seg.frame_rate
        play_obj = sa.play_buffer(raw_data, num_channels, bytes_per_sample, sample_rate)
        play_obj.wait_done()

        return {'ok': True, 'message': 'Poema reproducido correctamente'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}