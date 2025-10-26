import os
import json
import subprocess
import sys
import base64
import requests

def poem_tts(args: dict) -> dict:
    """Genera un poema y lo convierte a audio.
    - Intenta usar la API de ElevenLabs con la clave proporcionada.
    - Si la API falla (401, 429, timeout, etc.) se recurre a pyttsx3 local.
    - Oculta la clave API en cualquier mensaje de salida.
    - Devuelve el texto del poema y, si se generó audio, la ruta del archivo.
    """
    api_key = args.get("api_key", "")
    # No exponer la clave en logs
    safe_key = api_key[:4] + "..." + api_key[-4:] if api_key else ""
    # Poema simple (se puede extender con generación más avanzada)
    poem = """En la noche silente la luna susurra,\n\nLos sueños navegan en mares de plata,\n\nLa aurora despierta esperanzas renovadas,\n\nY el viento acaricia recuerdos perdidos."""
    result = {"poem": poem, "audio_path": None, "message": None}
    # Función de ayuda para guardar audio
    def _save_audio(content: bytes, ext: str) -> str:
        filename = f"poem_{os.urandom(4).hex()}.{ext}"
        path = os.path.join(os.getcwd(), filename)
        with open(path, "wb") as f:
            f.write(content)
        return path
    # Intento con ElevenLabs
    try:
        if not api_key:
            raise ValueError("API key no proporcionada")
        # Elección de voz por defecto (cambiar si se desea)
        voice_id = "EXAVITQu4vr4xnSDxMaL"  # voz predeterminada de ElevenLabs
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": poem,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            audio_path = _save_audio(response.content, "mp3")
            result["audio_path"] = audio_path
            # Reproducir (intenta usar ffplay si está disponible)
            try:
                # ffplay es parte de ffmpeg; se usa sin ventana
                subprocess.run(["ffplay", "-autoexit", "-nodisp", audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                # Si ffplay no está, ignorar reproducción silenciosamente
                pass
            result["message"] = "Audio generado con ElevenLabs."
            return result
        else:
            # Se considera error, pasamos al fallback
            raise RuntimeError(f"ElevenLabs error {response.status_code}")
    except Exception as e:
        # Manejo genérico del error, sin exponer la clave ni trazas técnicas
        result["message"] = "No se pudo generar audio con ElevenLabs; se usará síntesis local."
        # Intento fallback con pyttsx3
        try:
            # Instalar pyttsx3 si no está disponible
            try:
                import pyttsx3
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pyttsx3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                import pyttsx3
            engine = pyttsx3.init()
            # Configuración básica (voz, velocidad)
            engine.setProperty('rate', 150)
            audio_path = os.path.join(os.getcwd(), f"poem_{os.urandom(4).hex()}.wav")
            engine.save_to_file(poem, audio_path)
            engine.runAndWait()
            result["audio_path"] = audio_path
            # Reproducir usando simple play command (depends on OS)
            try:
                if sys.platform.startswith('win'):
                    os.startfile(audio_path)
                elif sys.platform.startswith('darwin'):
                    subprocess.run(["afplay", audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    # Linux: intenta usar aplay o ffplay
                    subprocess.run(["aplay", audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            result["message"] += " Audio generado localmente."
        except Exception:
            # Si el fallback también falla, simplemente devolvemos el poema
            result["message"] = "No se pudo generar audio ni con ElevenLabs ni con síntesis local."
        return result
