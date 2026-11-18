"""Acciones permitidas. Lista cerrada: no existe forma de mandar G-code libre.

Cada accion devuelve (descripcion_para_confirmar, funcion_a_ejecutar).
`prepare_*` valida y NO toca la impresora; solo `run` ejecuta.
"""
from . import config, moonraker as mr


class Refused(Exception):
    pass


def _busy(st):
    return st["state"] in ("printing", "paused")


def prepare_preheat(hotend, bed):
    if hotend is None and bed is None:
        raise Refused("Dime un material o las temperaturas.")
    if hotend is not None and not 0 < hotend <= config.MAX_HOTEND:
        raise Refused(f"El hotend no puede pasar de {int(config.MAX_HOTEND)} grados.")
    if bed is not None and not 0 < bed <= config.MAX_BED:
        raise Refused(f"La cama no puede pasar de {int(config.MAX_BED)} grados.")
    if _busy(mr.status()):
        raise Refused("Hay una impresion en curso, no cambio temperaturas.")
    parts, cmds = [], []
    if hotend is not None:
        parts.append(f"hotend a {int(hotend)}")
        cmds.append(f"M104 S{int(hotend)}")
    if bed is not None:
        parts.append(f"cama a {int(bed)}")
        cmds.append(f"M140 S{int(bed)}")
    return "precalentar " + " y ".join(parts), lambda: mr.gcode("\n".join(cmds))


def prepare_cooldown():
    if _busy(mr.status()):
        raise Refused("Hay una impresion en curso, no la enfrio.")
    return "apagar los calentadores", lambda: mr.gcode("M104 S0\nM140 S0")


def prepare_home():
    if _busy(mr.status()):
        raise Refused("Hay una impresion en curso, no hago home.")
    return "hacer home de todos los ejes (la maquina se movera)", lambda: mr.gcode("G28")


def prepare_pause():
    if mr.status()["state"] != "printing":
        raise Refused("No hay ninguna impresion en curso.")
    return "pausar la impresion", mr.pause


def prepare_resume():
    if mr.status()["state"] != "paused":
        raise Refused("No hay ninguna impresion pausada.")
    return "reanudar la impresion", mr.resume


def prepare_cancel():
    if not _busy(mr.status()):
        raise Refused("No hay ninguna impresion que cancelar.")
    return "cancelar la impresion, esto no se puede deshacer", mr.cancel
