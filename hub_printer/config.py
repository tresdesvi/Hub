import os


def _f(name, default):
    return float(os.environ.get(name, default))


MOONRAKER_URL = os.environ.get("MOONRAKER_URL", "http://192.168.1.50:7125").rstrip("/")
MOONRAKER_API_KEY = os.environ.get("MOONRAKER_API_KEY", "")  # opcional
ALEXA_SKILL_ID = os.environ.get("ALEXA_SKILL_ID", "")  # amzn1.ask.skill.xxxx
ALEXA_VERIFY = os.environ.get("ALEXA_VERIFY", "1") != "0"  # solo desactivar en pruebas locales
PORT = int(os.environ.get("PORT", "8080"))

# Limites duros: ninguna orden de voz puede superarlos.
MAX_HOTEND = _f("MAX_HOTEND", 260)
MAX_BED = _f("MAX_BED", 100)
CONFIRM_TTL = _f("CONFIRM_TTL", 45)  # segundos para responder "si"

# material -> (hotend, cama)
MATERIALS = {
    "pla": (210, 60),
    "petg": (240, 80),
    "abs": (260, 100),
    "asa": (260, 100),
    "tpu": (225, 50),
}
