import requests
import json
import io
import simpleaudio
from pydub import AudioSegment

def generate_and_play_poem(args: dict) -> dict:
    """
    Genera y reproduce un poema en audio usando ElevenLabs.
    Args:
        args: dict con la clave 'api_key'.
    Returns:
        dict con información del proceso y posibles errores.
    """
    api_key = args.get('api_key')
    if not api_key:
        return {'ok': False, 'error': 'API key missing in arguments'}

    headers = {'xi-api-key': api_key}
    try:
        # 1. Listar voces disponibles
        voice_list_resp = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers, timeout=15)
        if voice_list_resp.status_code == 401:
            return {'ok': False, 'error': 'Authorization failed (401). Verifica la API key.'}
        if voice_list_resp.status_code != 200:
            return {'ok': False, 'error': f'Error al listar voces: {voice_list_resp.status_code} {voice_list_resp.text}'}
        voices_data = voice_list_resp.json()
        voices = voices_data.get('voices', [])
        if not voices:
            return {'ok': False, 'error': 'No se encontraron voces en la cuenta.'}

        # Poema estático
        poem = (
            "En la quietud del alba, la luz se desliza,\n"
            "sobre el lago sereno que refleja la brisa.\n"
            "Cada ola susurra un verso sin final,\n"
            "y el sol escribe sueños en el cristal."
        )

        # Preparar datos de TTS
        tts_payload = {
            'text': poem,
            'model_id': 'eleven_monolingual_v1'
        }
        tts_headers = {
            **headers,
            'Accept': 'audio/mpeg',
            'Content-Type': 'application/json'
        }

        chosen_voice_id = None
        audio_content = None
        # Intentar con cada voz hasta obtener éxito
        for voice in voices:
            voice_id = voice.get('voice_id')
            if not voice_id:
                continue
            tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
            resp = requests.post(tts_url, headers=tts_headers, json=tts_payload, timeout=30)
            if resp.status_code == 200:
                chosen_voice_id = voice_id
                audio_content = resp.content
                break
            # Manejo de error específico de voz no encontrada
            if resp.status_code == 404 and 'voice_not_found' in resp.text:
                continue  # probar la siguiente voz
            # Otros errores abortan
            if resp.status_code == 401:
                return {'ok': False, 'error': 'Authorization failed during TTS (401).'}
            # Si llega aquí, otro error; intentar siguiente voz
        if not audio_content:
            return {'ok': False, 'error': 'No se pudo generar audio con ninguna voz disponible.'}

        # Convertir MP3 a WAV usando pydub
        try:
            audio_mp3 = io.BytesIO(audio_content)
            audio_seg = AudioSegment.from_file(audio_mp3, format='mp3')
            wav_io = io.BytesIO()
            audio_seg.export(wav_io, format='wav')
            wav_bytes = wav_io.getvalue()
        except Exception as e:
            return {'ok': False, 'error': f'Error convirtiendo MP3 a WAV: {str(e)}'}

        # Guardar archivo WAV
        filename = 'poem.wav'
        try:
            with open(filename, 'wb') as f:
                f.write(wav_bytes)
        except IOError as e:
            return {'ok': False, 'error': f'Error al guardar archivo WAV: {str(e)}'}

        # Reproducir audio con simpleaudio
        try:
            wave_obj = simpleaudio.WaveObject(
                wav_bytes,
                num_channels=audio_seg.channels,
                bytes_per_sample=audio_seg.sample_width,
                sample_rate=audio_seg.frame_rate
            )
            play_obj = wave_obj.play()
            play_obj.wait_done()
        except Exception as e:
            return {'ok': False, 'error': f'Error reproduciendo audio: {str(e)}'}

        return {
            'ok': True,
            'message': 'Poema generado y reproducido exitosamente.',
            'voice_id': chosen_voice_id,
            'file': filename
        }
    except Exception as ex:
        return {'ok': False, 'error': f'Excepción inesperada: {str(ex)}'}
