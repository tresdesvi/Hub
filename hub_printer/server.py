import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import config, skill


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/alexa":
            return self._send(404, {})
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            if config.ALEXA_VERIFY:
                from . import alexa_verify
                alexa_verify.verify(dict(self.headers), body)
            out = skill.handle(json.loads(body))
        except Exception as e:
            print("rechazada:", e, file=sys.stderr)
            return self._send(400, {"error": "bad request"})
        self._send(200, out)

    def _send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def main():
    if config.ALEXA_VERIFY and not config.ALEXA_SKILL_ID:
        sys.exit("Define ALEXA_SKILL_ID (o ALEXA_VERIFY=0 solo para pruebas locales).")
    print(f"Escuchando en :{config.PORT}  impresora: {config.MOONRAKER_URL}")
    ThreadingHTTPServer(("0.0.0.0", config.PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
