"""Salud del servicio y la regla de oro: ninguna prueba toca la base de desarrollo."""

import os

from django.conf import settings
from django.db import connection

from config.settings import _base_de_datos


def test_salud_responde_sin_token(api):
    r = api.get("/api/v1/salud")
    assert r.status_code == 200 and r.json()["estado"] == "ok"


class BaseCaida:
    def cursor(self):
        raise ConnectionError("la base no responde")


def test_salud_sin_base_de_datos_es_503(api, monkeypatch):
    from infraestructura.api import vistas

    monkeypatch.setattr(vistas, "connection", BaseCaida())
    r = api.get("/api/v1/salud")
    assert r.status_code == 503 and r.json()["codigo"] == "SERVICIO_NO_DISPONIBLE"


def test_la_base_de_estas_pruebas_es_efimera(db):
    """Regla de oro de la Guía 7: pytest-django crea una base nueva y la destruye al final."""
    usada = str(connection.settings_dict["NAME"])
    desarrollo = str(_base_de_datos(os.environ.get("DATABASE_URL"))["NAME"])  # la de todos los días
    assert usada != desarrollo
    assert "memory" in usada or usada == f"test_{desarrollo}", usada
    assert settings.EMAIL_BACKEND.endswith("locmem.EmailBackend")
