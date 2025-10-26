import os
import json
import requests
import tempfile

def generate_and_play_poem(args: dict) -> dict:
    """
    Genera un poema corto, lo convierte a audio usando ElevenLabs y lo reproduce.
    Args:
        args: dict con la clave 'api_key' (string)
    Returns:
        dict con 'ok' (bool) y 'file' (ruta del mp3) o 'error'.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'api_key no proporcionado'}

        # Poema generado
        poem = (
            "En la quietud del alba, el susurro del viento,\n"
            "Pinta de oro los sueños que el día lleva,\n"
            "Cada hoja, cada estrella, un momento,\n"
            "Y el corazón, latente, nunca queda."
        )

        # Parámetros de ElevenLabs (voice_id por defecto)
        voice_id = "EXAVITQu4vr4xnSDxMaL"  # voz en inglés, se usará igualmente
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": poem,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error de ElevenLabs: {response.status_code} {response.text}'}

        # Guardar audio en archivo temporal
        tmp_dir = tempfile.gettempdir()
        file_path = os.path.join(tmp_dir, 'poema.mp3')
        with open(file_path, 'wb') as f:
            f.write(response.content)

        # Reproducir el archivo (compatible con Windows y macOS/Linux)
        try:
            if os.name == 'nt':
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', file_path])
            else:
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            # Si falla la reproducción, no se considera crítico
            return {'ok': True, 'file': file_path, 'warning': f'Audio guardado pero no se pudo reproducir: {e}'}

        return {'ok': True, 'file': file_path}
    except Exception as e:
        return {'ok': False, 'error': str(e)}