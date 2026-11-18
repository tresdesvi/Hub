"""Verificacion de peticiones de Alexa (requisito de Amazon y proteccion real:
sin esto cualquiera con la URL podria precalentar tu impresora).

Comprueba: URL del certificado, firma RSA, vigencia y SAN del certificado,
antiguedad (<150 s) y applicationId. Requiere `cryptography`.
"""
import base64
import datetime
import json
import urllib.parse
import urllib.request

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from . import config

_certs = {}


class Invalid(Exception):
    pass


def _check_url(url):
    u = urllib.parse.urlparse(url)
    if not (u.scheme.lower() == "https" and u.hostname and u.hostname.lower() == "s3.amazonaws.com"
            and u.path.startswith("/echo.api/") and u.port in (None, 443)):
        raise Invalid("SignatureCertChainUrl invalida")


def _leaf(url):
    if url not in _certs:
        pem = urllib.request.urlopen(url, timeout=8).read()
        _certs[url] = x509.load_pem_x509_certificates(pem)[0]
    return _certs[url]


def verify(headers, body):
    h = {k.lower(): v for k, v in headers.items()}
    url = h.get("signaturecertchainurl", "")
    _check_url(url)
    cert = _leaf(url)
    now = datetime.datetime.now(datetime.timezone.utc)
    if not cert.not_valid_before_utc <= now <= cert.not_valid_after_utc:
        raise Invalid("certificado caducado")
    san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    if "echo-api.amazon.com" not in san.get_values_for_type(x509.DNSName):
        raise Invalid("certificado sin echo-api.amazon.com")
    if "signature-256" in h:
        sig, algo = h["signature-256"], hashes.SHA256()
    elif "signature" in h:
        sig, algo = h["signature"], hashes.SHA1()
    else:
        raise Invalid("sin firma")
    try:
        cert.public_key().verify(base64.b64decode(sig), body, padding.PKCS1v15(), algo)
    except Exception as e:
        raise Invalid("firma incorrecta") from e

    data = json.loads(body)
    ts = datetime.datetime.fromisoformat(data["request"]["timestamp"].replace("Z", "+00:00"))
    if abs((now - ts).total_seconds()) > 150:
        raise Invalid("peticion antigua")
    app = data["session"]["application"]["applicationId"]
    if not config.ALEXA_SKILL_ID or app != config.ALEXA_SKILL_ID:
        raise Invalid("skill id no coincide")
