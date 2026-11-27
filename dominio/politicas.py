"""Políticas del negocio que cambian según el gimnasio (Software III, Guía 03: Strategy).

La regla de quién anula un pago ya cambió una vez (ADR N.° 18) y un dueño puede preferir la
anterior. Por eso vive detrás de un contrato: `AnulacionPagoService` no sabe cuál le tocó.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol

from dominio.errores import PermisoDenegado
from dominio.modelos import ZONA_HORARIA, Pago, Usuario


class PoliticaAnulacion(Protocol):
    """Contrato: no devuelve nada si `usuario` puede anular `pago` hoy; si no, `PermisoDenegado`.

    Precondición: `usuario` es personal activo que puede anular (lo revisa el servicio antes).
    No cambia el pago ni consulta repositorios.
    """

    def exigir(self, pago: Pago, usuario: Usuario, hoy: date) -> None: ...


class RecepcionistaCorrigeSuDia:
    """ADR N.° 18, vigente: el administrador anula cualquiera; la recepcionista, lo suyo de hoy."""

    def exigir(self, pago: Pago, usuario: Usuario, hoy: date) -> None:
        if usuario.es_administrador():
            return
        registrado_hoy = pago.registrado_en.astimezone(ZONA_HORARIA).date() == hoy
        if pago.registrado_por.id != usuario.id or not registrado_hoy:
            raise PermisoDenegado(
                "La recepcionista solo puede anular los pagos que ella registró hoy."
            )


class SoloAdministradorAnula:
    """La regla anterior al ADR N.° 18 (su alternativa A): solo el administrador anula."""

    def exigir(self, pago: Pago, usuario: Usuario, hoy: date) -> None:
        if not usuario.es_administrador():
            raise PermisoDenegado("Solo el administrador puede anular pagos.")
