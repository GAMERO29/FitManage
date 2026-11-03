# Respuesta de la IA (sin modificar)

# Instrumentación de `registrar_pago` con OpenTelemetry

Son tres piezas: la configuración de OpenTelemetry (trazas, métricas y logs en JSON), el método instrumentado y la configuración de Django.

## 1. Dependencias

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc
```

## 2. Configuración de telemetría: `fitmanage/telemetria.py`

```python
import json
import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configurar_telemetria() -> None:
    """Inicializa trazas y métricas. El endpoint se toma de OTEL_EXPORTER_OTLP_ENDPOINT."""
    recurso = Resource.create({
        "service.name": os.getenv("OTEL_SERVICE_NAME", "fitmanage-backend"),
        "deployment.environment": os.getenv("DEPLOY_ENV", "production"),
    })

    proveedor_trazas = TracerProvider(resource=recurso)
    proveedor_trazas.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(proveedor_trazas)

    lector = PeriodicExportingMetricReader(OTLPMetricExporter(), export_interval_millis=15_000)
    metrics.set_meter_provider(MeterProvider(resource=recurso, metric_readers=[lector]))


# Atributos estándar de LogRecord; cualquier otro atributo viene de `extra=...`
RESERVADOS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    """Escribe cada log como una línea JSON, con trace_id y span_id si hay un span activo."""

    def format(self, record: logging.LogRecord) -> str:
        datos = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        contexto = trace.get_current_span().get_span_context()
        if contexto.is_valid:
            datos["trace_id"] = format(contexto.trace_id, "032x")
            datos["span_id"] = format(contexto.span_id, "016x")
        for clave, valor in record.__dict__.items():
            if clave not in RESERVADOS:
                datos[clave] = valor
        if record.exc_info:
            datos["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(datos, ensure_ascii=False, default=str)
```

## 3. Método instrumentado: `pagos/servicios.py`

Ajusta el import de los modelos a tu app.

```python
import hashlib
import logging
import time
from decimal import Decimal

from opentelemetry import metrics, trace

from .models import Pago, Plan, Socio  # ajusta a la ruta de tu app

logger = logging.getLogger("fitmanage.pagos")
tracer = trace.get_tracer("fitmanage.pagos")
meter = metrics.get_meter("fitmanage.pagos")

pagos_registrados = meter.create_counter(
    "fitmanage.pagos.registrados", unit="{pago}", description="Pagos registrados correctamente")
pagos_fallidos = meter.create_counter(
    "fitmanage.pagos.fallidos", unit="{pago}", description="Intentos de pago fallidos")
monto_pagos = meter.create_histogram(
    "fitmanage.pagos.monto", unit="COP", description="Monto de cada pago")
duracion_registro = meter.create_histogram(
    "fitmanage.pagos.duracion", unit="ms", description="Duración de registrar_pago")


def _hash_cedula(cedula: str) -> str:
    """Permite correlacionar eventos del mismo socio sin exponer la cédula."""
    return hashlib.sha256(cedula.encode()).hexdigest()[:12]


def registrar_pago(nombre: str, cedula: str, monto: Decimal, plan_id: str) -> Pago:
    inicio = time.perf_counter()
    socio_hash = _hash_cedula(cedula)

    with tracer.start_as_current_span("registrar_pago") as span:
        span.set_attributes({
            "fitmanage.socio.hash": socio_hash,
            "fitmanage.plan.id": str(plan_id),
            "fitmanage.pago.monto": float(monto),
        })
        try:
            socio = Socio.objects.get(numero_documento=cedula)
            plan = Plan.objects.get(id=plan_id)
            pago = Pago.objects.create(socio=socio, plan=plan, valor=monto)
        except Exception as exc:
            # El span ya queda en estado ERROR y registra la excepción
            # automáticamente, porque start_as_current_span lo hace por defecto.
            pagos_fallidos.add(1, {"error.type": type(exc).__name__})
            logger.exception(
                "Fallo al registrar pago",
                extra={
                    "evento": "pago_fallido",
                    "socio_hash": socio_hash,
                    "plan_id": str(plan_id),
                    "error_tipo": type(exc).__name__,
                },
            )
            raise
        else:
            span.set_attribute("fitmanage.pago.id", pago.id)
            pagos_registrados.add(1, {"plan.id": str(plan_id)})
            monto_pagos.record(float(monto), {"plan.id": str(plan_id)})
            logger.info(
                "Pago registrado",
                extra={
                    "evento": "pago_registrado",
                    "pago_id": pago.id,
                    "socio_hash": socio_hash,
                    "plan_id": str(plan_id),
                    "monto": float(monto),
                },
            )
            return pago
        finally:
            duracion_registro.record((time.perf_counter() - inicio) * 1000)
```

## 4. Configuración de Django

En `settings.py`, configura el logging con el formateador JSON:

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "fitmanage.telemetria.JsonFormatter"},
    },
    "handlers": {
        "consola": {"class": "logging.StreamHandler", "formatter": "json"},
    },
    "root": {"handlers": ["consola"], "level": "INFO"},
}
```

Luego inicializa la telemetría al arrancar la app, en `pagos/apps.py`:

```python
from django.apps import AppConfig


class PagosConfig(AppConfig):
    name = "pagos"

    def ready(self):
        from fitmanage.telemetria import configurar_telemetria
        configurar_telemetria()
```

Y define las variables de entorno, por ejemplo:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=fitmanage-backend
```

## Explicación breve

- **Span:** `registrar_pago` es una unidad de trabajo en la traza. Si `Socio.objects.get` o `Plan.objects.get` fallan, el span queda marcado como error con la excepción adjunta. Los logs incluyen el `trace_id`, así que puedes saltar de un log a su traza en tu herramienta de observabilidad.
- **Métricas:** un contador de pagos exitosos, otro de fallidos (etiquetado por tipo de error), un histograma de montos y otro de duración. Con ellas puedes ver tasas de error y latencia en el tiempo, algo que los logs solos no muestran bien.
- **Log JSON:** cada evento es una línea JSON con campos fijos (`evento`, `socio_hash`, `plan_id`, `pago_id`, etc.), lo que facilita filtrar en herramientas como Loki, Elasticsearch o CloudWatch.
- **Privacidad:** la cédula no se guarda en spans ni logs; se usa un hash truncado para correlacionar eventos. El parámetro `nombre` tampoco se registra. En tu código original no se usa: conviene revisar si falta incluirlo en la lógica o si puede eliminarse.
- **Gunicorn:** si usas `--preload`, los exportadores pueden no sobrevivir al fork de los workers. En ese caso llama a `configurar_telemetria()` dentro del hook `post_fork` de Gunicorn.
- **Opcional:** para instrumentar automáticamente las peticiones HTTP y las consultas de Django, puedes añadir `opentelemetry-instrumentation-django` y `opentelemetry-instrumentation-psycopg2` (o el driver que uses).
