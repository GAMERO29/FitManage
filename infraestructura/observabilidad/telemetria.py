"""OpenTelemetry para FitManage: un proveedor de trazas y uno de métricas por proceso (ADR N.° 13).

- Trazas: se muestrea el 10 % de las peticiones nuevas (OTEL_TRACES_SAMPLER_ARG); si la petición
  ya viene con una traza decidida por quien llama, se respeta esa decisión (ParentBased). Solo se
  exportan si existe OTEL_EXPORTER_OTLP_ENDPOINT; sin colector, igual hay trace_id para los logs.
- Métricas: se agregan en memoria y se leen en /metrics con el formato de Prometheus.
"""

from __future__ import annotations

import os
import threading

from django.conf import settings
from opentelemetry import metrics, trace
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, Sampler, TraceIdRatioBased

NOMBRE = "fitmanage"
PROPORCION_POR_DEFECTO = 0.1
# Límites de la latencia en segundos: QA-01 exige p95 < 2 s y hoy está cerca de 0,015 s.
LIMITES_LATENCIA = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0)

proporcion = PROPORCION_POR_DEFECTO
muestrear_todo = False  # solo lo cambian las pruebas
_proveedor: TracerProvider | None = None
_candado = threading.Lock()

# Se crean al importar, contra los proveedores «proxy» de OpenTelemetry: mientras nadie llame a
# configurar() no hacen nada, y después reportan al proveedor real. Con FITMANAGE_TELEMETRIA=0 el
# middleware no se instala, configurar() nunca corre y el costo es casi cero.
tracer = trace.get_tracer(NOMBRE)
_medidor = metrics.get_meter(NOMBRE)
duracion = _medidor.create_histogram(
    "http.server.request.duration",
    unit="s",
    description="Duración de las peticiones a la API",
    explicit_bucket_boundaries_advisory=LIMITES_LATENCIA,
)
consultas_estado = _medidor.create_counter(
    "fitmanage.consultas_estado",
    description="Consultas de estado en recepción, por resultado",
)


def proporcion_muestreo(valor: str | None) -> float:
    try:
        numero = float(valor) if valor is not None else PROPORCION_POR_DEFECTO
    except ValueError:
        return PROPORCION_POR_DEFECTO
    return numero if 0.0 <= numero <= 1.0 else PROPORCION_POR_DEFECTO


class _Raiz(Sampler):
    """TraceIdRatioBased que lee la proporción vigente en cada decisión."""

    def should_sample(self, parent_context, trace_id, name, kind=None, attributes=None, links=None):
        real = TraceIdRatioBased(1.0 if muestrear_todo else proporcion)
        return real.should_sample(parent_context, trace_id, name, kind, attributes, links)

    def get_description(self) -> str:
        return f"FitManageRatio{{{proporcion}}}"


def muestreador() -> ParentBased:
    return ParentBased(root=_Raiz())


def procesador_de_exportacion() -> BatchSpanProcessor | None:
    """OTLP por HTTP hacia el colector (Jaeger en compose); sin colector, las trazas no salen."""
    if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return None
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    return BatchSpanProcessor(OTLPSpanExporter())


def configurar() -> TracerProvider:
    global _proveedor, proporcion
    with _candado:
        if _proveedor is not None:
            return _proveedor
        proporcion = proporcion_muestreo(os.environ.get("OTEL_TRACES_SAMPLER_ARG"))
        recurso = Resource.create(
            {"service.name": NOMBRE, "service.version": settings.FITMANAGE_VERSION}
        )
        _proveedor = TracerProvider(resource=recurso, sampler=muestreador())
        exportacion = procesador_de_exportacion()
        if exportacion is not None:
            _proveedor.add_span_processor(exportacion)
        trace.set_tracer_provider(_proveedor)
        metrics.set_meter_provider(
            MeterProvider(resource=recurso, metric_readers=[PrometheusMetricReader()])
        )
        return _proveedor
