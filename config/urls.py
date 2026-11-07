"""Rutas: la API `/api/v1` del contrato (docs/api/openapi.yaml) y la pantalla de recepción."""

from django.urls import include, path

from infraestructura.observabilidad.vistas import metricas
from infraestructura.web import vistas as web

urlpatterns = [
    path("api/v1/", include("infraestructura.api.urls")),
    # Fuera de /api/v1 y del contrato: lo lee Prometheus, no los clientes (ADR N.° 13).
    path("metrics", metricas),
    # Guía 16 (ADR N.° 16): la pantalla de recepción consume la misma API del mismo origen.
    path("", web.recepcion),
    path("recepcion/<str:nombre>", web.recurso),
]
