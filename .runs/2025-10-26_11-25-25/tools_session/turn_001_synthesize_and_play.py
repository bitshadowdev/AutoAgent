import os
import json
import base64
import tempfile
import subprocess
import requests

def synthesize_and_play(args: dict) -> dict:
    """Genera un poema, lo convierte a audio con ElevenLabs y lo reproduce.
    Args:
        args: dict con claves
            - api_key (str): clave de API de ElevenLabs
            - voice_id (str, opcional): id de la voz a usar
    Returns:
        dict con resultado {'ok': bool, 'poem': str, 'audio_path': str, 'error': str (si falla)}
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'api_key es requerida'}
        voice_id = args.get('voice_id', 'EXAVITQu4vr4xnSDxMaL')  # voz predeterminada de ElevenLabs

        # Poema generado (puedes cambiarlo si lo deseas)
        poem = (
            "En la sombra del tiempo, susurra el viento,\n"
            "canta la luna su balada de plata,\n"
            "las estrellas derraman recuerdos,\n"
            "y el mar abraza la arena en su pecho."
        )

        # Llamada a la API de ElevenLabs
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": poem,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error en API ElevenLabs: {response.status_code} {response.text}'}

        audio_bytes = response.content
        # Guardar audio en archivo temporal
        tmp_dir = tempfile.gettempdir()
        audio_path = os.path.join(tmp_dir, f"poem_{voice_id}.mp3")
        with open(audio_path, 'wb') as f:
            f.write(audio_bytes)

        # Intentar reproducir el audio
        # Se intentan varios reproductores comunes según el SO
        played = False
        commands = []
        if os.name == 'nt':  # Windows
            commands.append(['cmd', '/c', 'start', '', audio_path])
        else:  # Unix/Linux/macOS
            commands.append(['ffplay', '-nodisp', '-autoexit', audio_path])
            commands.append(['mpg123', audio_path])
            commands.append(['afplay', audio_path])  # macOS
        for cmd in commands:
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                played = True
                break
            except Exception:
                continue
        if not played:
            # Si no se pudo reproducir, devolver audio en base64
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            return {
                'ok': True,
                'poem': poem,
                'audio_path': audio_path,
                'audio_base64': audio_b64,
                'message': 'Audio guardado pero no se encontró reproductor disponible.'
            }

        return {'ok': True, 'poem': poem, 'audio_path': audio_path}
    except Exception as e:
        return {'ok': False, 'error': str(e)}