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
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "infraestructura.persistencia",
]
ROOT_URLCONF = "config.urls"
STATIC_URL = "static/"

# ADR N.° 06: clave propia para firmar los JWT, distinta de SECRET_KEY y rotable con `kid`.
JWT_CLAVE = os.environ.get("JWT_CLAVE") or get_random_secret_key()
JWT_KID = os.environ.get("JWT_KID", "k1")
URL_PUBLICA = os.environ.get("FITMANAGE_URL_PUBLICA", "http://localhost:8000")

# Única dependencia externa de la API: el SMTP del hosting (DAD 8.2). Las pruebas usan
# el backend en memoria de Django; nunca se envía un correo real desde la suite.
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "1") == "1"
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "FitManage <no-responder@fitmanage.local>"
)


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
