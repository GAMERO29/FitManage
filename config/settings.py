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
# Render publica el nombre del servicio en RENDER_EXTERNAL_HOSTNAME; su healthcheck interno usa
# ese nombre. Así el despliegue no depende de copiar a mano el nombre exacto (ADR N.° 11).
if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])

INSTALLED_APPS = [
    "infraestructura.persistencia",
]
# Guía 13 (ADR N.° 13): una traza, una métrica y un log JSON por petición, sin datos personales.
# FITMANAGE_TELEMETRIA=0 la apaga sin tocar el código (por ejemplo, para medir cuánto cuesta).
TELEMETRIA = os.environ.get("FITMANAGE_TELEMETRIA", "1") != "0"
MIDDLEWARE = (
    ["infraestructura.observabilidad.middleware.MiddlewareTelemetria"] if TELEMETRIA else []
)
ROOT_URLCONF = "config.urls"

# Una línea JSON por evento en la salida estándar (Render la guarda y la muestra en su panel).
# El filtro redacta documentos y teléfonos también en los mensajes de Django y de las librerías.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"pii": {"()": "infraestructura.observabilidad.logs.FiltroPII"}},
    "formatters": {"json": {"()": "infraestructura.observabilidad.logs.FormateadorJSON"}},
    "handlers": {
        "json": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json",
            "filters": ["pii"],
        }
    },
    "root": {"handlers": ["json"], "level": os.environ.get("FITMANAGE_NIVEL_LOG", "INFO")},
}
STATIC_URL = "static/"

# ADR N.° 06: clave propia para firmar los JWT, distinta de SECRET_KEY y rotable con `kid`.
JWT_CLAVE = os.environ.get("JWT_CLAVE") or get_random_secret_key()
JWT_KID = os.environ.get("JWT_KID", "k1")
URL_PUBLICA = os.environ.get("FITMANAGE_URL_PUBLICA", "http://localhost:8000")
# ADR N.° 11: la imagen trae el SHA de su commit y /salud lo publica para el healthcheck.
FITMANAGE_VERSION = os.environ.get("FITMANAGE_VERSION", "desarrollo")

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
        # ADR N.° 08: conexiones persistentes. Con 0 se abre una conexión nueva en cada petición.
        "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
        "CONN_HEALTH_CHECKS": True,
        # Si la base no contesta, fallar en 10 s con un error claro en lugar de quedar colgado.
        "OPTIONS": {"connect_timeout": 10},
    }


DATABASES = {"default": _base_de_datos(os.environ.get("DATABASE_URL"))}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_TZ = True
