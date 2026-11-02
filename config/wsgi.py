"""Punto de entrada WSGI para gunicorn (despliegue y entorno de carga de la Guía 8)."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
