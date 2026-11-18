# Hub: Alexa ↔ Qidi Max3

Skill de Alexa propia (gratis, modo desarrollo, solo tu cuenta) que habla con Moonraker.
Sin Home Assistant, sin AWS, sin comprar nada.

## Que puedes decir
"Alexa, abre **mi impresora**" y luego:

| Consulta (sin confirmacion) | Orden (SIEMPRE pide confirmacion) |
|---|---|
| estado / cuanto falta | precalienta para PLA/PETG/ABS/ASA/TPU, o `hotend a N`, `cama a N` |
| temperaturas | enfria · haz home · pausa · reanuda · cancela la impresion |

Seguridad:
- Una orden solo se ejecuta tras responder "si" en la misma sesion, en menos de 45 s.
  Cualquier otra frase, un "no" o otra sesion la descartan.
- No existe G-code libre: solo la lista cerrada de `hub_printer/actions.py`.
- Limites duros (`MAX_HOTEND=260`, `MAX_BED=100`), y se rechazan precalentar/home/enfriar si hay impresion en curso.
- Cada peticion se verifica contra la firma de Amazon y tu `ALEXA_SKILL_ID`.

## Puesta en marcha
1. En un equipo de tu red que este siempre encendido (PC, Raspberry, NAS):
   ```
   pip install -r requirements.txt
   MOONRAKER_URL=http://IP_IMPRESORA:7125 ALEXA_SKILL_ID=amzn1.ask.skill.XXXX python -m hub_printer.server
   ```
   Comprueba antes que `http://IP_IMPRESORA:7125/printer/info` responde.
2. Dale una URL HTTPS publica **solo a `/alexa`** (gratis): Tailscale Funnel
   (`tailscale funnel 8080`, URL estable `*.ts.net`) o Cloudflare Tunnel.
   No expongas Moonraker.
3. En <https://developer.amazon.com/alexa/console/ask> crea una skill Custom, idioma
   es-ES, "Start from scratch". En *JSON Editor* pega `alexa/interaction_model_es.json`.
   En *Endpoint* elige HTTPS, pon tu URL + `/alexa` y tipo de certificado
   "trusted authority". Copia el Skill ID al paso 1 y reinicia el servicio.
4. En la pestana *Test* activa "Development" y prueba. Tambien funciona en tus Echo.

## Pruebas
`python -m unittest discover -s tests`

## Limites conocidos
- Probado solo con Moonraker simulado; no con tu Max3 ni con Alexa real.
  Qidi personaliza su firmware: si los nombres de objetos difieren, ajusta `moonraker.status()`.
- La cadena de certificados de Amazon no se valida hasta la raiz (solo hoja, vigencia, SAN y firma, con URL restringida a Amazon).
- El estado de confirmacion vive en memoria: reiniciar el servicio lo borra (seguro por defecto).
