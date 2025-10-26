import time
import random

def car_alarm_simulator(args: dict) -> dict:
    """Simula una alarma de coche.
    Args:
        args: {
            "duration": int (segundos totales de simulación, por defecto 10),
            "trigger_chance": float entre 0 y 1 probabilidad de que se active la alarma cada segundo (por defecto 0.3)
        }
    Returns:
        dict con clave 'ok' y 'log' (lista de eventos)."""
    try:
        duration = int(args.get('duration', 10))
        chance = float(args.get('trigger_chance', 0.3))
        if duration < 1:
            duration = 1
        log = []
        alarm_active = False
        log.append(f"Simulación iniciada: {duration}s, probabilidad de disparo {chance:.2f}")
        for sec in range(1, duration + 1):
            # Esperar un segundo (simulación rápida usando sleep 0.2 para no tardar mucho)
            time.sleep(0.2)
            if not alarm_active and random.random() < chance:
                alarm_active = True
                log.append(f"[t+{sec}s] Alarma ACTIVADA! Sirena encendida.")
            elif alarm_active and random.random() < 0.2:
                alarm_active = False
                log.append(f"[t+{sec}s] Alarma DESACTIVADA. Sirena apagada.")
            else:
                state = "ACTIVA" if alarm_active else "inactiva"
                log.append(f"[t+{sec}s] Alarma {state} (sin cambio).")
        log.append("Simulación finalizada.")
        return {"ok": True, "log": log}
    except Exception as e:
        return {"ok": False, "error": str(e)}