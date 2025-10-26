import requests
import os
import json
import tempfile
import subprocess

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo sintetiza con ElevenLabs y reproduce el audio.
    Args:
        args (dict): No se esperan parámetros, la función usa la API key
                    "sk_ba966103551a74998532d1201d01b69cc24887c879f5def3".
    Returns:
        dict: {'ok': True, 'file_path': <ruta>, 'message': <texto>} o {'ok': False, 'error': <msg>}
    """
    try:
        # ---------- 1. Poema ----------
        poem = (
            "En la quietud del alba, el sol despierta,\n"
            "Sus rayos dorados acarician la tierra,\n"
            "Los pájaros cantan, la brisa susurra,\n"
            "Un nuevo día, esperanza que se aferra."
        )

        # ---------- 2. Configuración de ElevenLabs ----------
        api_key = "sk_ba966103551a74998532d1201d01b69cc24887c879f5def3"
        voice_id = "EXAVITQu4vr4xnSDxMaL"  # voz predeterminada (Bella)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": poem,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }

        # ---------- 3. Llamada a la API ----------
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return {"ok": False, "error": f"API ElevenLabs error {response.status_code}: {response.text}"}
        audio_content = response.content

        # ---------- 4. Guardar archivo temporal ----------
        tmp_dir = tempfile.gettempdir()
        file_path = os.path.join(tmp_dir, "poema_elevenlabs.mp3")
        with open(file_path, "wb") as f:
            f.write(audio_content)

        # ---------- 5. Reproducir audio ----------
        # Intentar usar 'playsound', instalándolo si es necesario
        try:
            from playsound import playsound
        except ImportError:
            # Instalar playsound de forma silenciosa
            subprocess.check_call(["python", "-m", "pip", "install", "playsound==1.3.0", "--quiet"])
            from playsound import playsound
        # Reproducir (esto bloqueará hasta que termine la reproducción)
        playsound(file_path)

        return {"ok": True, "file_path": file_path, "message": "Poema generado y reproducido exitosamente."}
    except Exception as e:
        return {"ok": False, "error": str(e)}