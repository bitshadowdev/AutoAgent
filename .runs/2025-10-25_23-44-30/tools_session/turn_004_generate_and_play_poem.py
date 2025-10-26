import os
import json
import requests
import tempfile
import subprocess
import sys

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo convierte a audio con ElevenLabs y lo reproduce.
    Args:
        args: {
            "api_key": "string"  # clave de ElevenLabs
        }
    Returns:
        dict con claves 'ok' (bool) y opcionalmente 'file' (ruta del mp3) o 'error'.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {"ok": False, "error": "api_key faltante"}

        # --- Poema estático (se puede personalizar) ---
        poem = (
            "En la quietud de la noche, el silencio susurra,\n"
            "las estrellas dibujan caminos de luz,\n"
            "el viento lleva recuerdos de un sueño lejano,\n"
            "y el corazón late al ritmo del cosmos."
        )

        # --- Parámetros de ElevenLabs ---
        voice_id = "EXAVITQu4vr4xnSDxMaL"  # voz predeterminada de ElevenLabs
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}" 
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        payload = {"text": poem, "model_id": "eleven_monolingual_v1", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}

        # --- Solicitud a la API ---
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return {"ok": False, "error": f"Error de API ElevenLabs: {response.status_code} {response.text}"}

        # Guardar MP3 temporalmente
        tmp_dir = tempfile.gettempdir()
        mp3_path = os.path.join(tmp_dir, f"poema_{os.getpid()}.mp3")
        with open(mp3_path, "wb") as f:
            f.write(response.content)

        # --- Conversión MP3 -> WAV usando pydub (requiere ffmpeg) ---
        try:
            from pydub import AudioSegment
        except ImportError:
            # Instalar pydub y ffmpeg si falta
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pydub"])
            from pydub import AudioSegment
        # Asegurarse de que ffmpeg esté disponible
        if not AudioSegment.ffmpeg or not os.path.exists(AudioSegment.ffmpeg):
            # intentar instalar ffmpeg vía conda/pip no disponible; se asume que ffmpeg está en PATH
            pass
        wav_path = mp3_path.replace('.mp3', '.wav')
        audio = AudioSegment.from_file(mp3_path, format="mp3")
        audio.export(wav_path, format="wav")

        # --- Reproducción con simpleaudio ---
        try:
            import simpleaudio as sa
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "simpleaudio"])
            import simpleaudio as sa
        wave_obj = sa.WaveObject.from_wave_file(wav_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()

        return {"ok": True, "file": mp3_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}