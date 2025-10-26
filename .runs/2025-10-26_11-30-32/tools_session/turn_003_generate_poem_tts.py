import os
import json
import time
import requests
import pyttsx3

def generate_poem_tts(args: dict) -> dict:
    """Genera un poema y lo convierte a audio.
    Primero intenta usar la API de ElevenLabs; si falla, recurre a pyttsx3 local.
    La clave API no se incluye en la respuesta.
    """
    try:
        # ----- generar poema sencillo -----
        lines = [
            "En la quietud de la noche, la luna susurra",
            "Y el alba despierta esperanzas renovadas",
            "Los sueños navegan en mares de plata",
            "El viento acaricia recuerdos perdidos",
            "Y el corazón pulsa con ritmo silente"
        ]
        poem = "\n".join(lines)

        # ----- intentar ElevenLabs -----
        api_key = args.get('api_key')
        if api_key:
            try:
                voice_id = "EXAVITQu4vr4xnSDxMaL"
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "xi-api-key": api_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "text": poem,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=15)
                if resp.status_code == 200:
                    audio_path = f"/tmp/poem_{int(time.time())}.mp3"
                    with open(audio_path, "wb") as f:
                        f.write(resp.content)
                    return {"ok": True, "poem": poem, "audio_path": audio_path, "engine": "elevenlabs"}
                # Si no fue 200, lanzar para fallback
                raise Exception(f"ElevenLabs status {resp.status_code}")
            except Exception:
                # Ocultar detalles del error y pasar al fallback
                pass

        # ----- fallback con pyttsx3 -----
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        audio_path = f"/tmp/poem_{int(time.time())}_fallback.wav"
        engine.save_to_file(poem, audio_path)
        engine.runAndWait()
        return {"ok": True, "poem": poem, "audio_path": audio_path, "engine": "fallback"}
    except Exception as e:
        return {"ok": False, "error": "Unexpected error", "details": str(e)}