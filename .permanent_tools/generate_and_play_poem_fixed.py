import requests
import json
import simpleaudio as sa
import os
import tempfile

def generate_and_play_poem_fixed(args: dict) -> dict:
    """Genera un poema en audio con ElevenLabs y lo reproduce.
    Parámetros esperados en `args`:
        - api_key (str): clave API de ElevenLabs.
    Devuelve dict con 'ok' y 'message' o 'error'.
    """
    api_key = args.get('api_key')
    if not api_key:
        return {'ok': False, 'error': 'API key no provista.'}

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # 1. Listar voces disponibles
    try:
        resp = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers, timeout=15)
        if resp.status_code != 200:
            return {'ok': False, 'error': f'Error al listar voces: {resp.status_code} {resp.text}'}
        voices_data = resp.json()
        voices = voices_data.get('voices') or []
        if not voices:
            return {'ok': False, 'error': 'No se encontraron voces en la cuenta.'}
    except Exception as e:
        return {'ok': False, 'error': f'Excepción al listar voces: {str(e)}'}

    # Elegir la primera voz válida
    voice_id = None
    for v in voices:
        if v.get('voice_id'):
            voice_id = v['voice_id']
            break
    if not voice_id:
        return {'ok': False, 'error': 'No se encontró un voice_id válido en la lista.'}

    # Poema simple (se podría generar dinámicamente)
    poem = (
        "En la quietud del alba, el sol se asoma,\n"
        "Pintando de oro la tierra que toma.\n"
        "Canta el río su nota cristalina,\n"
        "Y el viento susurra una canción divina."
    )

    # 2. Solicitar generación de audio
    tts_url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream'
    payload = {
        'text': poem,
        'model_id': 'eleven_monolingual_v1',
        'voice_settings': {}
    }
    try:
        tts_resp = requests.post(tts_url, headers=headers, json=payload, timeout=30)
        if tts_resp.status_code == 404:
            # voice not found, intentar con otra voz
            for alt in voices[1:]:
                alt_id = alt.get('voice_id')
                if not alt_id:
                    continue
                alt_url = f'https://api.elevenlabs.io/v1/text-to-speech/{alt_id}/stream'
                alt_resp = requests.post(alt_url, headers=headers, json=payload, timeout=30)
                if alt_resp.status_code == 200:
                    tts_resp = alt_resp
                    break
            else:
                return {'ok': False, 'error': f'Voice not found y ninguna alternativa funcionó: {tts_resp.text}'}
        if tts_resp.status_code != 200:
            return {'ok': False, 'error': f'Error al generar audio: {tts_resp.status_code} {tts_resp.text}'}
        audio_bytes = tts_resp.content
    except Exception as e:
        return {'ok': False, 'error': f'Excepción al generar audio: {str(e)}'}

    # 3. Guardar audio a archivo temporal y reproducir
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        wave_obj = sa.WaveObject.from_wave_file(tmp_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()
        # Clean up file
        os.remove(tmp_path)
    except Exception as e:
        return {'ok': False, 'error': f'Error al reproducir audio: {str(e)}'}

    return {'ok': True, 'message': 'Poema generado y reproducido correctamente.'}