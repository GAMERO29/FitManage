"""Un span, una medición de latencia y una línea de log por cada petición a la API."""

from __future__ import annotations

import logging
import re
import time

from opentelemetry.trace import SpanKind

from infraestructura.observabilidad import telemetria

registro = logging.getLogger("fitmanage.peticiones")
_PARAMETRO = re.compile(r"<(?:\w+:)?(\w+)>")
# /salud la consulta el healthcheck cada pocos segundos y /metrics, Prometheus: no son tráfico.
_SIN_TELEMETRIA = ("/api/v1/salud", "/metrics")


def ruta_de(request) -> str:
    """La plantilla de la ruta, nunca la URL: así ningún documento entra a una etiqueta."""
    coincidencia = getattr(request, "resolver_match", None)
    if coincidencia is None or not coincidencia.route:
        return "sin_ruta"
    return "/" + _PARAMETRO.sub(r"{\1}", coincidencia.route)


class MiddlewareTelemetria:
    def __init__(self, get_response) -> None:
        self.get_response = get_response
        telemetria.configurar()

    def __call__(self, request):
        if request.path in _SIN_TELEMETRIA:
            return self.get_response(request)
        inicio = time.perf_counter()
        with telemetria.tracer.start_as_current_span(request.method, kind=SpanKind.SERVER) as span:
            respuesta = self.get_response(request)
            segundos = time.perf_counter() - inicio
            ruta = ruta_de(request)
            atributos = {
                "http.request.method": request.method,
                "http.route": ruta,
                "http.response.status_code": respuesta.status_code,
            }
            span.update_name(f"{request.method} {ruta}")
            span.set_attributes(atributos)
            telemetria.duracion.record(segundos, atributos)
            registro.info(
                "petición atendida",
                extra={
                    "evento": "peticion",
                    "metodo": request.method,
                    "ruta": ruta,
                    "estado": respuesta.status_code,
                    "duracion_ms": round(segundos * 1000, 2),
                    "muestreada": span.get_span_context().trace_flags.sampled,
                },
            )
        return respuesta
