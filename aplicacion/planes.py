"""Caso de uso CU-05 Gestionar planes (RF-02): el administrador crea, cambia y desactiva planes."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from dominio.auditoria import EventoAuditoria, TipoEvento
from dominio.errores import PermisoDenegado, PlanDuplicado, PlanNoDisponible, UltimoPlanActivo
from dominio.modelos import Plan, Usuario
from dominio.puertos import PlanRepositorio, RegistroAuditoria, Reloj, SinAuditoria


class GestionPlanesService:
    """Los cambios valen para los pagos que se registren después (RN-08).

    Los pagos ya registrados guardan su propia copia del valor y de las fechas, así que no cambian.
    Un plan no se borra: se desactiva (RN-09), y deja de ofrecerse en el formulario de pago.
    """

    def __init__(
        self,
        planes: PlanRepositorio,
        reloj: Reloj | None = None,
        auditoria: RegistroAuditoria | None = None,
    ) -> None:
        if auditoria is not None and reloj is None:
            raise ValueError("Para registrar la auditoría hace falta el reloj.")
        self._planes = planes
        self._reloj = reloj
        self._auditoria = auditoria or SinAuditoria()

    def crear(self, nombre: str, duracion_dias: int, precio: Decimal, solicitante: Usuario) -> Plan:
        self._exigir_administrador(solicitante)
        nombre = " ".join(nombre.split())
        if any(p.nombre.casefold() == nombre.casefold() for p in self._planes.todos()):
            raise PlanDuplicado(f"Ya hay un plan llamado {nombre}.")
        plan = Plan(nombre, duracion_dias, precio)
        self._planes.guardar(plan)
        self._registrar(
            TipoEvento.PLAN_CREADO,
            solicitante,
            plan,
            {"duracionDias": plan.duracion_dias, "precio": int(plan.precio)},
        )
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
        if nuevo.precio != actual.precio:  # RN-08: vale para los pagos que vengan
            self._registrar(
                TipoEvento.PRECIO_CAMBIADO,
                solicitante,
                nuevo,
                {"antes": int(actual.precio), "despues": int(nuevo.precio)},
            )
        if nuevo.activo != actual.activo:
            tipo = TipoEvento.PLAN_REACTIVADO if nuevo.activo else TipoEvento.PLAN_DESACTIVADO
            self._registrar(tipo, solicitante, nuevo, {})
        return nuevo

    def _registrar(self, tipo: TipoEvento, actor: Usuario, plan: Plan, extra: dict) -> None:
        if self._reloj is None:  # solo pasa con SinAuditoria: pruebas que no miran el rastro
            return
        detalle = {"plan": plan.nombre, **extra}
        self._auditoria.registrar(
            EventoAuditoria(tipo, actor, self._reloj.ahora(), plan.id, None, detalle)
        )

    def _activos(self) -> int:
        return sum(1 for p in self._planes.todos() if p.activo)

    @staticmethod
    def _exigir_administrador(solicitante: Usuario) -> None:
        if not solicitante.es_administrador():
            raise PermisoDenegado("Solo un administrador puede gestionar los planes.")
