import os
import requests
import io
import simpleaudio as sa
from pydub import AudioSegment

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo sintetiza con ElevenLabs y lo reproduce.
    Args:
        args: dict con la clave 'api_key' (string).
    Returns:
        dict con 'ok': bool y opcionalmente 'error' o 'message'.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'api_key no proporcionada'}

        # 1️⃣ Poema simple
        poema = (
            "En la aurora el sol despierta,\n"
            "y el cielo pinta su lienzo dorado.\n"
            "Los susurros del viento cuentan historias,\n"
            "mientras la tarde se vuelve canto."
        )

        # 2️⃣ Llamada a ElevenLabs (voz por defecto)
        voice_id = "21m00Tcm4TlvDq8ikWAM"  # voz de ejemplo (Rachel)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"  # sin /stream para obtener MP3 completo
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": poema,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error en ElevenLabs: {response.status_code} {response.text}'}

        # 3️⃣ Guardar MP3 en carpeta temporal
        temp_dir = os.path.join(os.getenv('TEMP') or '/tmp', 'elevenlabs')
        os.makedirs(temp_dir, exist_ok=True)
        mp3_path = os.path.join(temp_dir, 'poema.mp3')
        with open(mp3_path, 'wb') as f:
            f.write(response.content)
        if not os.path.exists(mp3_path):
            return {'ok': False, 'error': 'Fallo al guardar el archivo MP3'}

        # 4️⃣ Convertir MP3 a WAV en memoria
        wav_io = io.BytesIO()
        audio = AudioSegment.from_mp3(mp3_path)
        audio.export(wav_io, format='wav')
        wav_io.seek(0)

        # 5️⃣ Reproducir con simpleaudio
        wave_obj = sa.WaveObject.from_wave_file(wav_io)
        play_obj = wave_obj.play()
        play_obj.wait_done()

        return {'ok': True, 'message': 'Poema reproducido correctamente'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
