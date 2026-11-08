"""Aplicativo del personal (ADR N.° 16 y N.° 17): archivos estáticos que consumen /api/v1.

No usa plantillas ni la app de archivos estáticos de Django: son cinco archivos fijos (la página,
el script, la hoja de estilos y las dos fuentes del prototipo), leídos una vez al arrancar. La
política de contenido solo permite cargar y llamar al mismo origen, así que la
página no puede ejecutar scripts en línea ni mandar datos a otro dominio.
"""

from __future__ import annotations

from pathlib import Path

from django.http import Http404, HttpRequest, HttpResponse
from django.views.decorators.http import require_safe

CARPETA = Path(__file__).resolve().parent
ARCHIVOS = {
    "recepcion.html": "text/html; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
    "app.css": "text/css; charset=utf-8",
    "sora.woff2": "font/woff2",
    "atkinson.woff2": "font/woff2",
}
CONTENIDO = {nombre: (CARPETA / nombre).read_bytes() for nombre in ARCHIVOS}
POLITICA = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'; "
    "object-src 'none'"
)


def _archivo(nombre: str) -> HttpResponse:
    respuesta = HttpResponse(CONTENIDO[nombre], content_type=ARCHIVOS[nombre])
    respuesta["Content-Security-Policy"] = POLITICA
    respuesta["X-Content-Type-Options"] = "nosniff"
    respuesta["Referrer-Policy"] = "no-referrer"
    respuesta["Cache-Control"] = "no-cache"
    return respuesta


# GET y HEAD: los monitores de disponibilidad preguntan con HEAD (antes respondía 405).
@require_safe
def recepcion(request: HttpRequest) -> HttpResponse:
    return _archivo("recepcion.html")


@require_safe
def recurso(request: HttpRequest, nombre: str) -> HttpResponse:
    if nombre not in ARCHIVOS or nombre == "recepcion.html":
        raise Http404
    return _archivo(nombre)
