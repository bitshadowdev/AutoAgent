import requests
import simpleaudio
import os
import uuid
import json

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo convierte a audio con ElevenLabs y lo reproduce.
    Args:
        args: {
            "api_key": "clave de ElevenLabs"
        }
    Returns:
        dict con 'ok', 'audio_path' y posible 'error'.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'Falta la api_key'}

        # Poema simple (puede modificarse o generarse dinámicamente)
        poem = (
            "En la quietud de la noche, susurros de luz,\n"
            "las estrellas cantan al viento que fluye,\n"
            "el sueño despierta en alas de azul,\n"
            "y el corazón vibra con eco de esperanza."
        )

        # Voice ID predeterminado (Rachel de ElevenLabs)
        voice_id = "EXAVITQu4vr4xnLG5x6Hz"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": poem,
            "model_id": "eleven_monolingual_v1",
            "output_format": "wav"
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error del API ElevenLabs: {response.status_code} {response.text}'}

        # Guardar audio en archivo temporal
        audio_bytes = response.content
        audio_dir = os.path.abspath(os.path.join(os.getcwd(), "elevenlabs_audio"))
        os.makedirs(audio_dir, exist_ok=True)
        filename = f"poema_{uuid.uuid4().hex}.wav"
        audio_path = os.path.join(audio_dir, filename)
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)

        # Reproducir audio con simpleaudio
        wave_obj = simpleaudio.WaveObject.from_wave_file(audio_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()

        return {'ok': True, 'audio_path': audio_path}
    except Exception as e:
        return {'ok': False, 'error': str(e)}