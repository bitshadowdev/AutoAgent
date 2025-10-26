import numpy as np
import simpleaudio as sa

def play_beep(args: dict) -> dict:
    """Genera y reproduce un sonido de tono puro.
    Args:
        args: {
            "frequency": frecuencia en Hz (default 440),
            "duration": duración en segundos (default 1.0)
        }
    Returns:
        dict con 'ok' boolean y 'message' texto o 'error' en caso de fallo.
    """
    try:
        freq = float(args.get('frequency', 440))
        duration = float(args.get('duration', 1.0))
        # Parámetros de audio
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = np.sin(freq * t * 2 * np.pi)
        # Normalizar a 16-bit PCM
        audio = (wave * 32767).astype(np.int16)
        # Reproducir
        play_obj = sa.play_buffer(audio, 1, 2, sample_rate)
        play_obj.wait_done()
        return {"ok": True, "message": f"Beep reproducido: {freq}Hz por {duration}s"}
    except Exception as e:
        return {"ok": False, "error": str(e)}