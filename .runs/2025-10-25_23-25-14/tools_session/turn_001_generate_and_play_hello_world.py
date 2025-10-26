import requests
from pathlib import Path

def generate_and_play_hello_world(args: dict) -> dict:
    """Genera audio con ElevenLabs y lo reproduce.
    Args:
        args: {
            "api_key": "string",          # clave de ElevenLabs (requerida)
            "text": "string",             # texto a sintetizar (por defecto 'Hello world')
            "voice_id": "string",         # ID de voz (por defecto voz estándar)
            "output": "string"            # nombre de archivo MP3 a guardar (por defecto 'hello_world.mp3')
        }
    Returns:
        dict con 'ok' (bool) y, en caso de éxito, 'file' (ruta) o, en caso de error, 'error'.
    """
    api_key = args.get("api_key")
    if not api_key:
        return {"ok": False, "error": "api_key es obligatorio"}
    text = args.get("text", "Hello world")
    voice_id = args.get("voice_id", "21m00Tcm4TlvDq8ikWAM")  # voz predeterminada de ElevenLabs
    output_file = args.get("output", "hello_world.mp3")
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0, "similarity_boost": 0}
        }
        # Solicitud POST, streaming del audio
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
        response.raise_for_status()
        # Guardar contenido binario en archivo
        Path(output_file).write_bytes(response.content)
        # Intentar reproducir el audio
        try:
            from playsound import playsound
            playsound(output_file)
        except Exception as play_err:
            return {"ok": False, "error": f"Audio guardado pero falló la reproducción: {play_err}", "file": output_file}
        return {"ok": True, "file": output_file}
    except Exception as e:
        return {"ok": False, "error": str(e)}