"""/metrics para Prometheus, protegido con un token propio: las métricas describen el sistema."""

from __future__ import annotations

import hmac
import os

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest


@require_GET
def metricas(request: HttpRequest) -> HttpResponse:
    esperado = os.environ.get("FITMANAGE_METRICAS_TOKEN", "")
    if not esperado:
        return HttpResponse(status=404)  # sin token configurado, el endpoint no existe
    _, _, token = request.headers.get("Authorization", "").partition(" ")
    if not hmac.compare_digest(token.encode(), esperado.encode()):
        return HttpResponse(status=401, headers={"WWW-Authenticate": 'Bearer realm="metricas"'})
    return HttpResponse(generate_latest(REGISTRY), content_type=CONTENT_TYPE_LATEST)
