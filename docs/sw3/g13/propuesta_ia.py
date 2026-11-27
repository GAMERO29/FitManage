"""Salida de la IA, copiada sin cambios (fragmento relevante). NO se usa en FitManage.

Prompt: «Escribe en Python la regla de FitManage para saber si un usuario puede anular un pago:
el administrador siempre puede; la recepcionista solo si registró el pago ella misma y fue hoy.»
"""

from datetime import date


def puede_anular(pago, usuario):
    return usuario.rol == "ADMINISTRADOR" or (
        pago.registrado_por.nombre == usuario.nombre and pago.registrado_en.date() == date.today()  # noqa: DTZ011
    )
