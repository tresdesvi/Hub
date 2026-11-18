import json
import urllib.request

from . import config


class MoonrakerError(Exception):
    pass


def _req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(config.MOONRAKER_URL + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if config.MOONRAKER_API_KEY:
        req.add_header("X-Api-Key", config.MOONRAKER_API_KEY)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read() or b"{}")
    except Exception as e:  # red, timeout, 4xx/5xx
        raise MoonrakerError(str(e)) from e


def status():
    q = "print_stats&extruder&heater_bed&display_status&virtual_sdcard"
    s = _req("GET", "/printer/objects/query?" + q)["result"]["status"]
    ps = s["print_stats"]
    return {
        "state": ps.get("state", "unknown"),  # standby/printing/paused/complete/cancelled/error
        "file": ps.get("filename") or "",
        "elapsed": ps.get("print_duration", 0),
        "progress": s["virtual_sdcard"].get("progress", 0.0),
        "hotend": s["extruder"]["temperature"],
        "hotend_target": s["extruder"]["target"],
        "bed": s["heater_bed"]["temperature"],
        "bed_target": s["heater_bed"]["target"],
    }


def gcode(script):
    return _req("POST", "/printer/gcode/script", {"script": script})


def pause():
    return _req("POST", "/printer/print/pause")


def resume():
    return _req("POST", "/printer/print/resume")


def cancel():
    return _req("POST", "/printer/print/cancel")
