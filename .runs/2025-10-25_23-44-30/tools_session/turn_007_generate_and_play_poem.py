import os
import sys
import subprocess
import json
import requests
import tempfile
import io

# Aseguramos que los paquetes necesarios estén instalados
def _install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '--quiet'])

try:
    import simpleaudio as sa
except ImportError:
    _install('simpleaudio')
    import simpleaudio as sa

try:
    from pydub import AudioSegment
except ImportError:
    _install('pydub')
    from pydub import AudioSegment

def generate_and_play_poem(args: dict) -> dict:
    """Genera un poema, lo sintetiza con ElevenLabs y lo reproduce.
    Parámetros esperados en *args*:
        - api_key (str): clave de ElevenLabs.
    Devuelve dict con 'ok' y, en caso de error, 'error'.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'api_key no proporcionada'}

        # 1. Poema estático (puedes personalizarlo)
        poem = (
            "En la quietud del alba, susurra el viento,\n"
            "Lleva consigo sueños de origen y tiempo,\n"
            "Las hojas bailan, doradas, en su movimiento,\n"
            "Y el sol, tímido, pinta de oro el firmamento."
        )

        # 2. Preparar petición a ElevenLabs
        voice_id = 'EXAVITQu4vr4xnSDxMaL'  # voz predeterminada en inglés, funciona para texto en español también
        url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream'
        headers = {
            'Accept': 'audio/mpeg',
            'xi-api-key': api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            'text': poem,
            'model_id': 'eleven_monolingual_v1',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.75
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error de API ElevenLabs: {response.status_code} - {response.text}'}

        # 3. Guardar MP3 en carpeta temporal
        temp_dir = tempfile.gettempdir()
        os.makedirs(temp_dir, exist_ok=True)
        mp3_path = os.path.join(temp_dir, 'poema.mp3')
        with open(mp3_path, 'wb') as f:
            f.write(response.content)
        if not os.path.exists(mp3_path):
            return {'ok': False, 'error': 'No se pudo crear el archivo MP3'}

        # 4. Convertir MP3 a WAV (simpleaudio solo soporta WAV)
        wav_path = os.path.join(temp_dir, 'poema.wav')
        audio_seg = AudioSegment.from_file(mp3_path, format='mp3')
        audio_seg.export(wav_path, format='wav')
        if not os.path.exists(wav_path):
            return {'ok': False, 'error': 'Conversión a WAV falló'}

        # 5. Reproducir el WAV usando simpleaudio
        wave_obj = sa.WaveObject.from_wave_file(wav_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()

        return {'ok': True, 'mp3': mp3_path, 'wav': wav_path}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
