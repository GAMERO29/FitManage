"""Caso de uso CU-05 Gestionar planes (RF-02): el administrador crea, cambia y desactiva planes."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from dominio.errores import PermisoDenegado, PlanDuplicado, PlanNoDisponible, UltimoPlanActivo
from dominio.modelos import Plan, Usuario
from dominio.puertos import PlanRepositorio


class GestionPlanesService:
    """Los cambios valen para los pagos que se registren después (RN-08).

    Los pagos ya registrados guardan su propia copia del valor y de las fechas, así que no cambian.
    Un plan no se borra: se desactiva (RN-09), y deja de ofrecerse en el formulario de pago.
    """

    def __init__(self, planes: PlanRepositorio) -> None:
        self._planes = planes

    def crear(self, nombre: str, duracion_dias: int, precio: Decimal, solicitante: Usuario) -> Plan:
        self._exigir_administrador(solicitante)
        nombre = " ".join(nombre.split())
        if any(p.nombre.casefold() == nombre.casefold() for p in self._planes.todos()):
            raise PlanDuplicado(f"Ya hay un plan llamado {nombre}.")
        plan = Plan(nombre, duracion_dias, precio)
        self._planes.guardar(plan)
        return plan

    def cambiar(
        self,
        plan_id: UUID,
        solicitante: Usuario,
        precio: Decimal | None = None,
        activo: bool | None = None,
    ) -> Plan:
        self._exigir_administrador(solicitante)
        actual = self._planes.obtener(plan_id)
        if actual is None:
            raise PlanNoDisponible("El plan no existe.")
        if activo is False and actual.activo and self._activos() == 1:
            raise UltimoPlanActivo("Debe quedar al menos un plan activo para poder cobrar.")
        nuevo = Plan(
            actual.nombre,
            actual.duracion_dias,
            actual.precio if precio is None else precio,
            actual.activo if activo is None else activo,
            id=actual.id,
        )
        self._planes.guardar(nuevo)
        return nuevo

    def _activos(self) -> int:
        return sum(1 for p in self._planes.todos() if p.activo)

    @staticmethod
    def _exigir_administrador(solicitante: Usuario) -> None:
        if not solicitante.es_administrador():
            raise PermisoDenegado("Solo un administrador puede gestionar los planes.")
