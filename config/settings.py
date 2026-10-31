"""Configuración mínima de Django para los adaptadores de FitManage (ADR N.° 03 y 04)."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

# Nunca hay una clave escrita en el código: viene del entorno (en producción, del PaaS).
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or get_random_secret_key()
DEBUG = os.environ.get("DJANGO_DEBUG") == "1"
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "infraestructura.persistencia",
]


def _base_de_datos(url: str | None) -> dict:
    """DATABASE_URL=postgresql://usuario:clave@host:5432/base; sin ella, SQLite local."""
    if not url:
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "fitmanage.sqlite3"}
    partes = urlparse(url)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": partes.path.lstrip("/"),
        "USER": unquote(partes.username or ""),
        "PASSWORD": unquote(partes.password or ""),
        "HOST": partes.hostname or "",
        "PORT": str(partes.port or 5432),
    }


DATABASES = {"default": _base_de_datos(os.environ.get("DATABASE_URL"))}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_TZ = True
