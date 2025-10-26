import os
import json
import sys
import requests
import tempfile
from pathlib import Path

# Intentamos importar dependencias opcionales; si fallan, informamos al usuario
try:
    from gtts import gTTS
except Exception as e:
    gtts_import_error = str(e)
    gTTS = None
    gtts_import_error_msg = f"Error al importar gTTS: {e}"
else:
    gtts_import_error = None
    gtts_import_error_msg = None

try:
    from playsound import playsound
except Exception as e:
    playsound_import_error = str(e)
    playsound = None
    playsound_import_error_msg = f"Error al importar playsound: {e}"
else:
    playsound_import_error = None
    playsound_import_error_msg = None


def _verify_elevenlabs_key(api_key: str) -> dict:
    """Comprueba que la clave sea válida realizando una petición ligera.
    Devuelve dict con 'valid': bool y 'error' opcional.
    """
    url = "https://api.elevenlabs.io/v1/models"
    headers = {"xi-api-key": api_key}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return {"valid": True}
        else:
            return {
                "valid": False,
                "status": resp.status_code,
                "detail": resp.text
            }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def _generate_poem() -> str:
    """Genera un poema sencillo en español."""
    # Para evitar complejidad, usamos un poema estático.
    return (
        "En la quietud del alba, susurros de luz,\n"
        "el río canta historias que el viento traduce.\n"
        "Las hojas bailan al ritmo del tiempo,\n"
        "y el corazón late, libre, sin lamento."
    )


def _synthesize_elevenlabs(text: str, api_key: str) -> dict:
    """Intenta sintetizar voz con ElevenLabs.
    Retorna dict con 'ok' y 'audio_path' o 'error'.
    """
    # Usaremos la voz por defecto de ElevenLabs (puede cambiar).
    voice_id = "EXAVITQu4vr4xnSDxMaL"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        if resp.status_code == 200:
            # Guardamos el contenido binario en un archivo temporal
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmp.write(resp.content)
            tmp.close()
            return {"ok": True, "audio_path": tmp.name}
        else:
            return {
                "ok": False,
                "status": resp.status_code,
                "detail": resp.text
            }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _synthesize_gtts(text: str, lang: str = "es") -> dict:
    """Genera audio usando gTTS como fallback.
    Retorna dict con 'ok' y 'audio_path' o 'error'.
    """
    if gTTS is None:
        return {"ok": False, "error": gtts_import_error_msg or "gTTS no está disponible"}
    try:
        tts = gTTS(text=text, lang=lang)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(tmp.name)
        return {"ok": True, "audio_path": tmp.name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _play_audio(file_path: str) -> dict:
    """Reproduce el archivo MP3 usando playsound.
    Retorna dict con 'ok' o 'error'.
    """
    if playsound is None:
        return {"ok": False, "error": playsound_import_error_msg or "playsound no está disponible"}
    try:
        abs_path = os.path.abspath(file_path)
        # playsound espera una cadena sin comillas extra
        playsound(abs_path)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def generate_and_play_poem(args: dict) -> dict:
    """Entrada: {'api_key': '...'}
    Salida: dict JSON‑serializable con el resultado.
    """
    api_key = args.get("api_key")
    if not api_key:
        return {"ok": False, "error": "Se requiere la clave API de ElevenLabs bajo la clave 'api_key'."}

    # Paso 1: validar la clave
    key_check = _verify_elevenlabs_key(api_key)
    if not key_check.get("valid"):
        # Si la clave es inválida o falla la petición, usamos gTTS directamente
        error_msg = key_check.get("error") or f"Clave inválida (status {key_check.get('status')}): {key_check.get('detail')}"
        # Generamos poema y usamos gTTS como fallback
        poem = _generate_poem()
        synth = _synthesize_gtts(poem)
        if not synth.get("ok"):
            return {"ok": False, "error": f"Clave API inválida y fallback gTTS falló: {error_msg}; detalle fallback: {synth.get('error')}"}
        audio_path = synth["audio_path"]
        play_res = _play_audio(audio_path)
        if not play_res.get("ok"):
            return {"ok": False, "error": f"Clave API inválida y audio generado con gTTS, pero falló la reproducción: {play_res.get('error')}", "audio_path": audio_path}
        return {"ok": True, "message": "Poema generado con gTTS (clave ElevenLabs inválida)", "audio_path": audio_path}

    # Paso 2: clave válida, generar poema
    poem = _generate_poem()

    # Paso 3: intentar ElevenLabs
    synth = _synthesize_elevenlabs(poem, api_key)
    if not synth.get("ok"):
        # Fallback a gTTS
        synth = _synthesize_gtts(poem)
        if not synth.get("ok"):
            return {"ok": False, "error": f"Fallo ElevenLabs ({synth.get('status', '')}): {synth.get('detail', '')} y fallback gTTS también falló: {synth.get('error')}"}
    audio_path = synth["audio_path"]

    # Paso 4: reproducir audio
    play_res = _play_audio(audio_path)
    if not play_res.get("ok"):
        return {"ok": False, "error": f"Audio generado pero la reproducción falló: {play_res.get('error')}", "audio_path": audio_path}

    return {"ok": True, "message": "Poema generado y reproducido exitosamente", "audio_path": audio_path}
