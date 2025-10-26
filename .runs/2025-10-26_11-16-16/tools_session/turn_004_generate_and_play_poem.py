import requests
import json
import os
import simpleaudio as sa

def generate_and_play_poem(args: dict) -> dict:
    """Genera y reproduce un poema usando ElevenLabs.
    Args:
        args: dict con clave 'api_key' (str).
    Returns:
        dict con 'ok' (bool) y 'message' o 'error'.
    """
    try:
        api_key = args.get('api_key', '').strip()
        if not api_key:
            return {'ok': False, 'error': 'API key no provista.'}

        headers = {'xi-api-key': api_key}
        # Paso 1: validar la API key listando voces
        voice_list_url = 'https://api.elevenlabs.io/v1/voices'
        resp = requests.get(voice_list_url, headers=headers, timeout=10)
        if resp.status_code == 401:
            return {'ok': False, 'error': 'Authorization failed (401). Verifica la API key.'}
        if resp.status_code != 200:
            return {'ok': False, 'error': f'Error al listar voces: {resp.status_code} {resp.text}'}
        data = resp.json()
        voices = data.get('voices', [])
        if not voices:
            return {'ok': False, 'error': 'No se encontraron voces disponibles en la cuenta.'}
        voice_id = voices[0].get('voice_id')
        if not voice_id:
            return {'ok': False, 'error': 'La primera voz no tiene voice_id.'}

        # Paso 2: generar poema (texto estático)
        poem = (
            "En la quietud del alba, susurra el viento,\n"
            "Pinta de oro el horizonte, tierno y lento.\n"
            "Las sombras se despiden, el día renace,\n"
            "Y en cada rayo, un sueño abrazace."
        )

        # Paso 3: solicitar texto a voz (format WAV)
        tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
        payload = {
            'text': poem,
            'model_id': 'eleven_monolingual_v1',
            'output_format': 'wav',
            'voice_settings': {}
        }
        tts_headers = {
            'xi-api-key': api_key,
            'Content-Type': 'application/json',
            'Accept': 'audio/wav'
        }
        tts_resp = requests.post(tts_url, headers=tts_headers, json=payload, timeout=20)
        if tts_resp.status_code == 401:
            return {'ok': False, 'error': 'Authorization failed (401) al generar audio. Verifica la API key.'}
        if tts_resp.status_code == 404:
            # voice_not_found, intentar con siguiente voz si existe
            for v in voices[1:]:
                alt_id = v.get('voice_id')
                if not alt_id:
                    continue
                alt_url = f'https://api.elevenlabs.io/v1/text-to-speech/{alt_id}'
                alt_resp = requests.post(alt_url, headers=tts_headers, json=payload, timeout=20)
                if alt_resp.status_code == 200:
                    tts_resp = alt_resp
                    break
            else:
                return {'ok': False, 'error': 'voice_not_found y no hay voces alternativas.'}
        if tts_resp.status_code != 200:
            return {'ok': False, 'error': f'Error al generar audio: {tts_resp.status_code} {tts_resp.text}'}

        # Paso 4: guardar archivo WAV
        wav_path = 'poem.wav'
        try:
            with open(wav_path, 'wb') as f:
                f.write(tts_resp.content)
        except IOError as e:
            return {'ok': False, 'error': f'Error al escribir el archivo WAV: {str(e)}'}

        # Paso 5: reproducir con simpleaudio
        try:
            wave_obj = sa.WaveObject.from_wave_file(wav_path)
            play_obj = wave_obj.play()
            play_obj.wait_done()
        except Exception as e:
            return {'ok': False, 'error': f'Error al reproducir audio: {str(e)}'}

        return {'ok': True, 'message': 'Poema reproducido exitosamente.', 'audio_file': os.path.abspath(wav_path)}
    except Exception as exc:
        return {'ok': False, 'error': f'Excepción inesperada: {str(exc)}'}
