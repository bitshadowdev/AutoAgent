import subprocess, sys, json, numpy as np, time

def play_beep(args: dict) -> dict:
    """Genera y reproduce un beep de 440 Hz durante 0.5 s.
    Parámetros (opcional):
        frequency (int): frecuencia en Hz (default 440)
        duration (float): duración en segundos (default 0.5)
    Retorna dict con 'ok' y 'message'."""
    try:
        # Intentar importar simpleaudio, instalar si falta
        try:
            import simpleaudio as sa
        except ImportError:
            # instalar simpleaudio y numpy si es necesario
            subprocess.check_call([sys.executable, "-m", "pip", "install", "simpleaudio", "numpy", "--quiet"])
            import simpleaudio as sa
            import numpy as np
        # leer argumentos
        freq = int(args.get('frequency', 440))
        dur = float(args.get('duration', 0.5))
        # generar onda sinusoidal
        sample_rate = 44100
        t = np.linspace(0, dur, int(sample_rate * dur), False)
        tone = np.sin(freq * t * 2 * np.pi)
        audio = (tone * 32767).astype(np.int16)  # 16‑bit PCM
        # reproducir
        play_obj = sa.play_buffer(audio, 1, 2, sample_rate)
        play_obj.wait_done()
        return {"ok": True, "message": f"Beep reproducido ({freq} Hz, {dur}s)."}
    except Exception as e:
        return {"ok": False, "error": str(e)}