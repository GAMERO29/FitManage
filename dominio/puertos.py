"""Puertos (interfaces) que el dominio necesita del exterior.

La infraestructura los implementa (Django ORM, reloj de Bogotá); las pruebas
usan dobles en memoria. El dominio nunca importa Django ni la base de datos.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from dominio.modelos import Pago, Plan, Socio, TipoDocumento


class SocioRepositorio(Protocol):
    def buscar_por_documento(self, tipo: TipoDocumento, numero: str) -> Socio | None: ...

    def guardar(self, socio: Socio) -> None: ...


class PlanRepositorio(Protocol):
    def obtener(self, plan_id: UUID) -> Plan | None: ...


class PagoRepositorio(Protocol):
    def vigentes_de(self, socio: Socio) -> list[Pago]: ...

    def existe_referencia_vigente(self, referencia: str) -> bool: ...

    def guardar(self, pago: Pago) -> None: ...


class Reloj(Protocol):
    """Entrega la fecha y hora en la zona America/Bogota (RN-03)."""

    def hoy(self) -> date: ...

    def ahora(self) -> datetime: ...
