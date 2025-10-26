import requests
import base64

def elevenlabs_synthesize(args: dict) -> dict:
    """Genera audio a partir de texto usando la API de ElevenLabs.
    Args:
        args: {
            "api_key": "str",  # clave de ElevenLabs
            "voice_id": "str",  # ID de la voz (se usará una voz predeterminada si no se especifica)
            "text": "str",       # texto a sintetizar
            "model_id": "str"    # modelo a usar (opcional)
        }
    Returns:
        dict con "ok": bool, "audio_base64": str (si ok) o "error": str.
    """
    try:
        api_key = args.get("api_key")
        if not api_key:
            return {"ok": False, "error": "Missing api_key"}
        text = args.get("text", "")
        if not text:
            return {"ok": False, "error": "Missing text"}
        voice_id = args.get("voice_id", "21m00Tcm4TlvDq8ikWAM")  # voz predeterminada de ElevenLabs
        model_id = args.get("model_id", "eleven_multilingual_v2")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}" 
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            return {"ok": False, "error": f"API error {response.status_code}: {response.text}"}
        audio_bytes = response.content
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        return {"ok": True, "audio_base64": audio_b64}
    except Exception as e:
        return {"ok": False, "error": str(e)}