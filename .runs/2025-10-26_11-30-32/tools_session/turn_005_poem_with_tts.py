import os
import json
import uuid
import requests
import simpleaudio as sa
import pyttsx3

def poem_with_tts(args: dict) -> dict:
    # Clave API embebida (no se expone en la salida)
    API_KEY = "sk_62c428bc9f293165a5a2c472fb2487f234a68137b9292f8f"
    VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Voice default
    # Poema sencillo
    poem = (
        "En la quietud de la noche, la luna susurra,\n"
        "Y el alba despierta esperanzas renovadas.\n"
        "Los sueños navegan en mares de plata,\n"
        "El viento acaricia recuerdos perdidos."
    )
    # Ruta temporal para el audio
    audio_file = os.path.join(os.getcwd(), f"poem_{uuid.uuid4().hex}.wav")
    # Intentar ElevenLabs
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        data = {
            "text": poem,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=15)
        if resp.status_code == 200:
            # Guardar audio (convertir MP3 a WAV usando pydub si disponible)
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(io.BytesIO(resp.content), format="mp3")
                audio.export(audio_file, format="wav")
            except Exception:
                # Si pydub no está disponible, guardar como mp3 y renombrar (simpleaudio solo lee wav)
                mp3_path = audio_file.replace('.wav', '.mp3')
                with open(mp3_path, "wb") as f:
                    f.write(resp.content)
                # Intentar convertir con ffmpeg si está en el sistema
                import subprocess, shlex
                cmd = f"ffmpeg -y -i {shlex.quote(mp3_path)} {shlex.quote(audio_file)}"
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if not os.path.isfile(audio_file):
                    raise RuntimeError("Conversión a WAV falló")
        else:
            raise RuntimeError(f"ElevenLabs error: {resp.status_code}")
    except Exception as e:
        # Fallback a pyttsx3 local
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.save_to_file(poem, audio_file)
            engine.runAndWait()
        except Exception as fallback_err:
            return {
                "ok": False,
                "error": "No se pudo generar audio ni con ElevenLabs ni con TTS local.",
                "poem": poem
            }
    # Reproducir audio
    try:
        wave_obj = sa.WaveObject.from_wave_file(audio_file)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as play_err:
        return {
            "ok": True,
            "poem": poem,
            "audio_path": audio_file,
            "message": "Audio generado, pero la reproducción falló."
        }
    return {
        "ok": True,
        "poem": poem,
        "audio_path": audio_file,
        "message": "Poema generado y reproducido exitosamente."
    }