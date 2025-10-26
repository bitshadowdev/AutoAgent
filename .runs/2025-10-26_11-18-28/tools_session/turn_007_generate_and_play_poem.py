import os
import json
import sys
import requests
import tempfile

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo sintetiza con ElevenLabs (fallback gTTS) y reproduce el audio.
    Parámetros esperados en *args*:
        - api_key (str): clave de ElevenLabs.
    Retorna dict con 'ok': bool y, en caso de error, 'error' y opcionalmente 'detail'."""
    # ------------------------------------------------------------
    # Validar argumentos
    # ------------------------------------------------------------
    api_key = args.get('api_key')
    if not api_key:
        return {"ok": False, "error": "Falta la API key de ElevenLabs en los argumentos."}

    # ------------------------------------------------------------
    # Función auxiliar para instalar paquetes opcionales dinámicamente
    # ------------------------------------------------------------
    def _ensure_package(pkg_name, import_name=None):
        try:
            if import_name:
                __import__(import_name)
            else:
                __import__(pkg_name)
            return True, None
        except ImportError:
            try:
                import subprocess, sys as _sys
                subprocess.check_call([_sys.executable, "-m", "pip", "install", pkg_name])
                if import_name:
                    __import__(import_name)
                else:
                    __import__(pkg_name)
                return True, None
            except Exception as e:
                return False, str(e)

    # ------------------------------------------------------------
    # 1. Verificar la clave mediante una petición ligera
    # ------------------------------------------------------------
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        resp = requests.get("https://api.elevenlabs.io/v1/models", headers=headers, timeout=10)
        if resp.status_code == 401 or resp.status_code == 403:
            return {"ok": False, "error": "Clave API de ElevenLabs inválida o sin permisos.", "status": resp.status_code}
        elif resp.status_code != 200:
            return {"ok": False, "error": "Error inesperado al validar la API key.", "status": resp.status_code, "detail": resp.text}
    except Exception as e:
        return {"ok": False, "error": "Excepción al validar la API key.", "detail": str(e)}

    # ------------------------------------------------------------
    # 2. Generar poema (texto simple)
    # ------------------------------------------------------------
    poem = (
        "En la quietud de la noche, la luna susurra,\n"
        "y las estrellas cantan su luz en la sombra.\n"
        "El viento lleva versos de antiguos mares,\n"
        "y el corazón escucha el latir del tiempo."
    )

    # ------------------------------------------------------------
    # 3. Intentar generar audio con ElevenLabs
    # ------------------------------------------------------------
    audio_path = None
    eleven_success = False
    voice_id = "EXAVITQu4vr4xnSDxMaL"  # Voice predeterminada (puede cambiarse)
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "text": poem,
        "model_id": "eleven_multilingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    try:
        tts_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        tts_resp = requests.post(tts_url, headers=tts_headers, json=payload, stream=True, timeout=30)
        if tts_resp.status_code == 200:
            fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            with open(tmp_path, "wb") as f:
                for chunk in tts_resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            audio_path = tmp_path
            eleven_success = True
        else:
            # Si la respuesta no es 200, capturamos el mensaje para fallback
            eleven_error_detail = tts_resp.text
    except Exception as e:
        eleven_error_detail = str(e)

    # ------------------------------------------------------------
    # 4. Fallback a gTTS si ElevenLabs falla
    # ------------------------------------------------------------
    if not eleven_success:
        # Intentar importar/instalar gTTS
        ok_pkg, err_pkg = _ensure_package("gtts")
        if not ok_pkg:
            return {"ok": False, "error": "Fallo al usar ElevenLabs y no se pudo instalar gTTS.", "detail": err_pkg}
        from gtts import gTTS
        try:
            fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            tts = gTTS(text=poem, lang="es")
            tts.save(tmp_path)
            audio_path = tmp_path
        except Exception as e:
            return {"ok": False, "error": "Falló el fallback a gTTS.", "detail": str(e)}

    # ------------------------------------------------------------
    # 5. Reproducir el audio con playsound (instalar si falta)
    # ------------------------------------------------------------
    if not audio_path or not os.path.isfile(audio_path):
        return {"ok": False, "error": "Archivo de audio no encontrado después del proceso de síntesis."}

    # Asegurarnos que la ruta sea absoluta y sin comillas extra
    audio_path = os.path.abspath(audio_path)
    ok_pkg, err_pkg = _ensure_package("playsound", "playsound")
    if not ok_pkg:
        return {"ok": False, "error": "No se pudo instalar la librería playsound para reproducir audio.", "detail": err_pkg}
    from playsound import playsound
    try:
        playsound(audio_path)
        return {"ok": True, "audio_path": audio_path, "used_fallback": not eleven_success, "eleven_error": (eleven_error_detail if not eleven_success else None)}
    except Exception as e:
        return {"ok": False, "error": "Error al reproducir el audio.", "detail": str(e), "audio_path": audio_path}
