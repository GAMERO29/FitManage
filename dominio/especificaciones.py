"""Especificaciones del dominio (Software III, Guía 13).

Una especificación responde «¿este candidato cumple el criterio?» y se combina con `&`, `|` y `~`.
La primera es quién puede anular un pago (RF-10 v1.3, ADR N.° 18):

    PUEDE_ANULAR = EsAdministrador() | (LoRegistroQuienAnula() & RegistradoElMismoDia())

Es una disyunción a propósito: el administrador no necesita cumplir las otras dos. Con una
conjunción, el administrador tampoco podría anular un pago de ayer.
La usan la política (para rechazar) y el historial (para avisarle a la pantalla qué se puede
anular). Antes, la pantalla repetía la regla en JavaScript comparando nombres.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from dominio.modelos import ZONA_HORARIA, Pago, Usuario


class Especificacion:
    def es_satisfecha_por(self, candidato) -> bool:
        raise NotImplementedError

    def __and__(self, otra: Especificacion) -> Especificacion:
        return _Combinada("y", lambda c: self.es_satisfecha_por(c) and otra.es_satisfecha_por(c))

    def __or__(self, otra: Especificacion) -> Especificacion:
        return _Combinada("o", lambda c: self.es_satisfecha_por(c) or otra.es_satisfecha_por(c))

    def __invert__(self) -> Especificacion:
        return _Combinada("no", lambda c: not self.es_satisfecha_por(c))


class _Combinada(Especificacion):
    def __init__(self, nombre: str, criterio: Callable[[object], bool]) -> None:
        self.nombre, self._criterio = nombre, criterio

    def es_satisfecha_por(self, candidato) -> bool:
        return self._criterio(candidato)


@dataclass(frozen=True)
class SolicitudAnulacion:
    """El candidato: quién quiere anular qué pago y qué día es en Bogotá."""

    pago: Pago
    usuario: Usuario
    hoy: date


class EsAdministrador(Especificacion):
    def es_satisfecha_por(self, s: SolicitudAnulacion) -> bool:
        return s.usuario.es_administrador()


class LoRegistroQuienAnula(Especificacion):
    """Se compara por identidad (`id`), no por nombre: dos personas pueden llamarse igual."""

    def es_satisfecha_por(self, s: SolicitudAnulacion) -> bool:
        return s.pago.registrado_por.id == s.usuario.id


class RegistradoElMismoDia(Especificacion):
    """El día del registro en Bogotá: las 23:59:59 cuentan, las 00:00:00 del día siguiente no."""

    def es_satisfecha_por(self, s: SolicitudAnulacion) -> bool:
        return s.pago.registrado_en.astimezone(ZONA_HORARIA).date() == s.hoy


PUEDE_ANULAR = EsAdministrador() | (LoRegistroQuienAnula() & RegistradoElMismoDia())
