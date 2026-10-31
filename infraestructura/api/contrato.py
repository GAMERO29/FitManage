"""El contrato OpenAPI valida cada solicitud antes de que llegue al caso de uso.

Así hay una sola fuente de verdad para formatos y campos obligatorios: `docs/api/openapi.yaml`.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.http import HttpRequest
from openapi_core import Config, OpenAPI
from openapi_core.contrib.django import DjangoOpenAPIRequest
from openapi_core.validation.request.exceptions import SecurityValidationError

RUTA_CONTRATO = Path(settings.BASE_DIR) / "docs" / "api" / "openapi.yaml"


@lru_cache(maxsize=1)
def especificacion() -> OpenAPI:
    # problem+json (RFC 9457) es JSON, pero openapi-core no lo trae registrado.
    config = Config(extra_media_type_deserializers={"application/problem+json": json.loads})
    return OpenAPI.from_file_path(str(RUTA_CONTRATO), config=config)


def _detalles(error: Exception) -> list[dict]:
    causa = error.__cause__ or error
    subs = getattr(causa, "schema_errors", None) or []
    if not subs:
        return [{"campo": getattr(causa, "name", "solicitud"), "mensaje": str(causa)}]
    return [
        {"campo": ".".join(str(p) for p in sub.path) or "cuerpo", "mensaje": sub.message}
        for sub in subs
    ]


def revisar(request: HttpRequest) -> tuple[bool, list[dict]]:
    """Devuelve (falta_credencial, errores). Sin errores, la solicitud cumple el contrato."""
    resultado = especificacion().unmarshal_request(DjangoOpenAPIRequest(request))
    falta_credencial = False
    errores: list[dict] = []
    for error in resultado.errors:
        if isinstance(error, SecurityValidationError):
            falta_credencial = True
        else:
            errores.extend(_detalles(error))
    return falta_credencial, errores
