"""Caso de uso de planes: el administrador cambia el precio (CU-05, RF-02)."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from dominio.errores import PermisoDenegado, PlanNoDisponible
from dominio.modelos import Plan, Usuario
from dominio.puertos import PlanRepositorio


class CambioPrecioService:
    """El precio nuevo vale para los pagos que se registren después (RN-08).

    Los pagos ya registrados guardan su propia copia del valor, así que no cambian.
    """

    def __init__(self, planes: PlanRepositorio) -> None:
        self._planes = planes

    def cambiar_precio(self, plan_id: UUID, precio: Decimal, solicitante: Usuario) -> Plan:
        if not solicitante.es_administrador():
            raise PermisoDenegado("Solo un administrador puede cambiar precios.")
        actual = self._planes.obtener(plan_id)
        if actual is None:
            raise PlanNoDisponible("El plan no existe.")
        nuevo = Plan(actual.nombre, actual.duracion_dias, precio, actual.activo, id=actual.id)
        self._planes.guardar(nuevo)
        return nuevo
