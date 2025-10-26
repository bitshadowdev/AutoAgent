import os
import sys
import json
import tempfile
import subprocess
import requests

def validate_and_synthesize_poem(args: dict) -> dict:
    """Valida la clave API de ElevenLabs, genera un poema, lo sintetiza y reproduce el audio.
    Retorna un dict JSON‑serializable con los resultados.
    """
    # ---------------------------------------------------------------------
    # 1. Obtención y saneamiento de la API key
    # ---------------------------------------------------------------------
    api_key = str(args.get('api_key', '')).strip()
    if not api_key:
        return {"ok": False, "error": "API key no proporcionada o está vacía."}

    headers = {"Authorization": f"Bearer {api_key}"}

    # ---------------------------------------------------------------------
    # 2. Validación ligera de la clave (GET /v1/user)
    # ---------------------------------------------------------------------
    try:
        validation_resp = requests.get(
            "https://api.elevenlabs.io/v1/user",
            headers=headers,
            timeout=10
        )
        if validation_resp.status_code == 401:
            return {"ok": False, "error": "Clave API de ElevenLabs inválida o expirada (401)."}
        validation_resp.raise_for_status()
    except requests.RequestException as exc:
        return {"ok": False, "error": f"Error de red al validar la API key: {exc}"}

    # ---------------------------------------------------------------------
    # 3. Generación del poema (texto estático, pero puede ser aleatorio)
    # ---------------------------------------------------------------------
    poem = (
        "En la quietud del alba se alza el susurro,\n"
        "de los sueños que la noche dejó atrás,\n"
        "las estrellas pintan caminos de luz,\n"
        "y el horizonte despliega su paz.\n"
        "\n"
        "Escucha el viento, lleva mi verso,\n"
        "sobre ríos de tiempo y mar de cristal,\n"
        "que cada palabra sea un universo,\n"
        "y que la voz lo haga inmortal."
    )

    # ---------------------------------------------------------------------
    # 4. Síntesis del texto a audio mediante ElevenLabs
    # ---------------------------------------------------------------------
    voice_id = "EXAVITQu4vr4xnSDxMaL"  # Voz por defecto de ElevenLabs
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "text": poem,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    try:
        tts_resp = requests.post(
            tts_url,
            headers={**headers, "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        if tts_resp.status_code == 401:
            return {"ok": False, "error": "Clave API inválida durante la síntesis (401)."}
        tts_resp.raise_for_status()
    except requests.RequestException as exc:
        return {"ok": False, "error": f"Error de red al sintetizar el audio: {exc}"}

    # ---------------------------------------------------------------------
    # 5. Guardado del audio en un archivo temporal
    # ---------------------------------------------------------------------
    try:
        tmp_dir = tempfile.gettempdir()
        audio_path = os.path.join(tmp_dir, "poem.mp3")
        with open(audio_path, "wb") as f:
            f.write(tts_resp.content)
    except Exception as exc:
        return {"ok": False, "error": f"No se pudo guardar el archivo de audio: {exc}"}

    # ---------------------------------------------------------------------
    # 6. Reproducción del audio (método dependiente del SO)
    # ---------------------------------------------------------------------
    try:
        if os.name == "nt":  # Windows
            subprocess.run(["cmd", "/c", "start", "", audio_path], check=False)
        elif sys.platform == "darwin":  # macOS
            subprocess.run(["afplay", audio_path], check=False)
        else:  # Linux y otros
            subprocess.run(["xdg-open", audio_path], check=False)
    except Exception:
        # No es crítico si la reproducción falla; se sigue devolviendo el archivo.
        pass

    return {
        "ok": True,
        "poem": poem,
        "audio_path": audio_path,
        "message": "Poema generado, sintetizado y reproducido (si el sistema lo permite)."
    }