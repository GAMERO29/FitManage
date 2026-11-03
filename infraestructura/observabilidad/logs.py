"""Logs de una línea en JSON, con el trace_id de la petición y sin datos personales."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from opentelemetry import trace

from infraestructura.observabilidad.privacidad import redactar

# Lista blanca: un campo que no esté aquí no sale, aunque alguien lo pase en `extra`.
CAMPOS = (
    "evento",
    "metodo",
    "ruta",
    "estado",
    "duracion_ms",
    "resultado",
    "tipo_documento",
    "seudonimo",
    "muestreada",
    "version",
)


class FiltroPII(logging.Filter):
    """Última barrera: también limpia los mensajes de Django y de las librerías."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redactar(record.getMessage())
        record.args = None
        return True


class FormateadorJSON(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        linea = {
            "momento": datetime.fromtimestamp(record.created, UTC).isoformat(
                timespec="milliseconds"
            ),
            "nivel": record.levelname,
            "logger": record.name,
            "mensaje": redactar(record.getMessage()),
        }
        contexto = trace.get_current_span().get_span_context()
        if contexto.is_valid:
            linea["trace_id"] = format(contexto.trace_id, "032x")
            linea["span_id"] = format(contexto.span_id, "016x")
        for campo in CAMPOS:
            if hasattr(record, campo):
                linea[campo] = getattr(record, campo)
        if record.exc_info:
            linea["excepcion"] = redactar(self.formatException(record.exc_info))
        return json.dumps(linea, ensure_ascii=False)
