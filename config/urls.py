"""Rutas de FitManage. Por ahora solo la API `/api/v1` del contrato (docs/api/openapi.yaml)."""

from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("infraestructura.api.urls")),
]
