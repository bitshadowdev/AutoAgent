import numpy as np
import simpleaudio as sa

def play_beep(args: dict) -> dict:
    """Reproduce un sonido de tipo beep.
    Parámetros opcionales en *args*:
      - frequency (Hz): frecuencia del tono, por defecto 440 Hz.
      - duration (seconds): duración del tono, por defecto 1 segundo.
    Devuelve dict con 'ok' y mensaje o error.
    """
    try:
        freq = float(args.get('frequency', 440))
        duration = float(args.get('duration', 1.0))
        fs = 44100  # tasa de muestreo
        t = np.linspace(0, duration, int(fs * duration), False)
        tone = np.sin(freq * t * 2 * np.pi)
        # Normalizar a 16‑bit PCM
        audio = tone * (2**15 - 1) / np.max(np.abs(tone))
        audio = audio.astype(np.int16)
        # Reproducir
        play_obj = sa.play_buffer(audio, 1, 2, fs)
        play_obj.wait_done()
        return {
            'ok': True,
            'message': f'Beep reproducido: {freq} Hz durante {duration} s.'
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)}