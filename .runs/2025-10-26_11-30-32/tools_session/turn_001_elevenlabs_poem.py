import os
import json
import requests
import subprocess

def elevenlabs_poem(args: dict) -> dict:
    """Genera un poema, lo sintetiza con ElevenLabs y lo reproduce.
    Args:
        args: dict con la clave 'api_key' (string).
    Returns:
        dict con 'ok': bool, 'poem': str, 'audio_file': str (ruta), y 'error' opcional.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'Falta la api_key'}
        # 1️⃣ Poema estático (se puede personalizar)
        poem = (
            "En la quietud del alba, susurra el viento,\n"
            "Pintando de luz la sombra del tiempo.\n"
            "Las hojas cantan, danzan sin quebranto,\n"
            "Y el corazón late, libre, en su canto."
        )
        # 2️⃣ Parámetros ElevenLabs
        voice_id = "EXAVITQu4vr4xnSDxMaL"  # voz predeterminada en ElevenLabs
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": poem,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            "output_format": "wav"
        }
        # 3️⃣ Solicitud a ElevenLabs
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error en ElevenLabs: {response.status_code} {response.text}'}
        # 4️⃣ Guardar audio en archivo temporal
        audio_path = os.path.join(os.getcwd(), "poem.wav")
        with open(audio_path, 'wb') as f:
            f.write(response.content)
        # 5️⃣ Reproducir audio usando ffplay (de ffmpeg) o, si no está, usar el comando por defecto del SO
        try:
            # Intentamos reproducir con ffplay (silencioso y autoclosed)
            subprocess.run(["ffplay", "-autoexit", "-nodisp", audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception:
            # Fallback: usar 'start' en Windows, 'open' en macOS, 'xdg-open' en Linux
            if os.name == 'nt':
                os.startfile(audio_path)
            elif sys.platform == 'darwin':
                subprocess.run(["open", audio_path])
            else:
                subprocess.run(["xdg-open", audio_path])
        return {'ok': True, 'poem': poem, 'audio_file': audio_path}
    except Exception as e:
        return {'ok': False, 'error': str(e)}