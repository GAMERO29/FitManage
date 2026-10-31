"""Fechas de prueba siempre con zona horaria de Bogotá (RN-03)."""

from datetime import datetime

from dominio.modelos import ZONA_HORARIA


def bogota(*partes: int) -> datetime:
    return datetime(*partes, tzinfo=ZONA_HORARIA)
