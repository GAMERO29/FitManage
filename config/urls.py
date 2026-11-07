"""Rutas de FitManage. Por ahora solo la API `/api/v1` del contrato (docs/api/openapi.yaml)."""

from django.urls import include, path

from infraestructura.observabilidad.vistas import metricas

urlpatterns = [
    path("api/v1/", include("infraestructura.api.urls")),
    # Fuera de /api/v1 y del contrato: lo lee Prometheus, no los clientes (ADR N.° 13).
    path("metrics", metricas),
]
