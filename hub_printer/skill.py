"""Logica de la skill de Alexa (es-ES). Sin dependencias de red salvo Moonraker."""
import threading
import time

from . import actions, config, moonraker as mr

_pending = {}  # session_id -> (expira, descripcion, funcion)
_lock = threading.Lock()


def _say(text, end=True):
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": text},
            "shouldEndSession": end,
        },
    }


def _num(slots, name):
    v = (slots.get(name) or {}).get("value")
    try:
        return float(v) if v is not None else None
    except ValueError:
        return None


def _mins(seconds):
    m = int(seconds // 60)
    return f"{m // 60} horas y {m % 60} minutos" if m >= 60 else f"{m} minutos"


def _status_text():
    s = mr.status()
    names = {"standby": "en reposo", "printing": "imprimiendo", "paused": "en pausa",
             "complete": "con la impresion terminada", "cancelled": "con la impresion cancelada",
             "error": "en error"}
    t = f"La impresora esta {names.get(s['state'], s['state'])}."
    if s["state"] in ("printing", "paused"):
        p = s["progress"]
        t += f" Va al {int(p * 100)} por ciento."
        if p > 0.01:
            t += f" Quedan unos {_mins(s['elapsed'] / p * (1 - p))}."
    return t


def _temps_text():
    s = mr.status()

    def one(nombre, cur, tgt):
        base = f"{nombre} a {int(cur)} grados"
        return base + (f", objetivo {int(tgt)}" if tgt else "")

    return one("El hotend", s["hotend"], s["hotend_target"]) + ". " + \
        one("La cama", s["bed"], s["bed_target"]) + "."


def _ask_confirm(session_id, prepared):
    desc, fn = prepared
    with _lock:
        _pending[session_id] = (time.time() + config.CONFIRM_TTL, desc, fn)
    return _say(f"Voy a {desc}. ¿Lo confirmas?", end=False)


def handle(event):
    req = event["request"]
    sid = event["session"]["sessionId"]
    try:
        if req["type"] == "LaunchRequest":
            return _say("Dime que necesitas: estado, temperaturas, precalentar o pausar.", end=False)
        if req["type"] != "IntentRequest":
            return _say("")
        name = req["intent"]["name"]
        slots = req["intent"].get("slots") or {}

        # --- confirmacion: unica via de ejecucion ---
        if name in ("AMAZON.YesIntent", "AMAZON.NoIntent"):
            with _lock:
                exp, desc, fn = _pending.pop(sid, (0, "", None))
            if fn is None or time.time() > exp:
                return _say("No hay nada pendiente de confirmar.")
            if name == "AMAZON.NoIntent":
                return _say("Vale, no hago nada.")
            fn()
            return _say(f"Hecho: {desc}.")

        # Cualquier otra frase descarta una confirmacion pendiente.
        with _lock:
            _pending.pop(sid, None)

        if name == "EstadoIntent":
            return _say(_status_text())
        if name == "TemperaturaIntent":
            return _say(_temps_text())
        if name == "PrecalentarIntent":
            mat = ((slots.get("material") or {}).get("value") or "").lower()
            hot, bed = _num(slots, "hotend"), _num(slots, "cama")
            if mat in config.MATERIALS and hot is None and bed is None:
                hot, bed = config.MATERIALS[mat]
            return _ask_confirm(sid, actions.prepare_preheat(hot, bed))
        if name == "EnfriarIntent":
            return _ask_confirm(sid, actions.prepare_cooldown())
        if name == "HomeIntent":
            return _ask_confirm(sid, actions.prepare_home())
        if name == "PausarIntent":
            return _ask_confirm(sid, actions.prepare_pause())
        if name == "ReanudarIntent":
            return _ask_confirm(sid, actions.prepare_resume())
        if name == "CancelarImpresionIntent":
            return _ask_confirm(sid, actions.prepare_cancel())
        if name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
            return _say("Hasta luego.")
        return _say("No te he entendido. Puedes pedir estado, temperaturas o precalentar.", end=False)
    except actions.Refused as e:
        return _say(str(e))
    except mr.MoonrakerError:
        return _say("No consigo hablar con la impresora. Revisa que este encendida y conectada.")
