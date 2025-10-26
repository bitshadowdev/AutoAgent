import numpy as np
import simpleaudio as sa

def play_beep(args: dict) -> dict:
    """Genera y reproduce un tono sinusoidal.
    Args:
        args: {
            'frequency': frecuencia en Hz (por defecto 440),
            'duration': duración en segundos (por defecto 1),
            'volume': volumen entre 0.0 y 1.0 (por defecto 0.5)
        }
    Returns:
        dict con 'ok' y opcionalmente 'error'.
    """
    try:
        freq = float(args.get('frequency', 440))
        dur = float(args.get('duration', 1.0))
        vol = float(args.get('volume', 0.5))
        if not (0.0 <= vol <= 1.0):
            raise ValueError('volume must be between 0.0 and 1.0')
        sample_rate = 44100
        t = np.linspace(0, dur, int(sample_rate * dur), False)
        tone = np.sin(freq * t * 2 * np.pi)
        audio = tone * (32767 * vol)
        audio = audio.astype(np.int16)
        play_obj = sa.play_buffer(audio, 1, 2, sample_rate)
        play_obj.wait_done()
        return {'ok': True, 'message': f'Beep reproducido: {freq}Hz durante {dur}s'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}