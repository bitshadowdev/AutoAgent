import os
import requests
import io
import uuid
import simpleaudio as sa
from pydub import AudioSegment

def generate_and_play_poem_new(args: dict) -> dict:
    """Genera un poema, lo convierte a audio con ElevenLabs y lo reproduce.
    args debe contener:
        - api_key: str, la clave de API de ElevenLabs.
    """
    try:
        api_key = args.get('api_key')
        if not api_key:
            return {'ok': False, 'error': 'api_key no provisto'}

        # 1. Poema estático (puede ajustarse)
        poem = (
            "En la quietud del alba, susurra el viento,\n"
            "pintando sombras doradas sobre el tiempo.\n"
            "Cada hoja, un verso, cada río, canción,\n"
            "el mundo danza al ritmo del corazón."
        )

        # 2. Preparar carpeta temporal
        temp_dir = os.path.join(os.getenv('TEMP') or '/tmp', 'elevenlabs_audio')
        os.makedirs(temp_dir, exist_ok=True)

        # 3. Llamada a ElevenLabs TTS
        voice_id = "21m00Tcm4TlvDq8ikWAM"  # voz predeterminada (puede cambiar)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            'xi-api-key': api_key,
            'Content-Type': 'application/json'
        }
        data = {
            'text': poem,
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.75
            }
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            return {'ok': False, 'error': f'Error API ElevenLabs: {response.status_code} {response.text}'}

        # 4. Guardar MP3
        mp3_filename = f"{uuid.uuid4()}.mp3"
        mp3_path = os.path.join(temp_dir, mp3_filename)
        with open(mp3_path, 'wb') as f:
            f.write(response.content)
        if not os.path.exists(mp3_path):
            return {'ok': False, 'error': 'MP3 no guardado correctamente'}

        # 5. Convertir a WAV
        wav_filename = f"{uuid.uuid4()}.wav"
        wav_path = os.path.join(temp_dir, wav_filename)
        audio_seg = AudioSegment.from_file(mp3_path, format='mp3')
        audio_seg.export(wav_path, format='wav')
        if not os.path.exists(wav_path):
            return {'ok': False, 'error': 'WAV no generado correctamente'}

        # 6. Reproducir con simpleaudio
        wave_obj = sa.WaveObject.from_wave_file(wav_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()

        return {'ok': True, 'mp3_path': mp3_path, 'wav_path': wav_path}
    except Exception as e:
        return {'ok': False, 'error': str(e)}