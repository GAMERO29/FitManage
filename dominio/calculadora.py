"""Reglas de fechas y estado de la membresía (RN-03, RN-04 y RN-05)."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta

from dominio.modelos import EstadoMembresia, Pago

UN_DIA = timedelta(days=1)


class CalculadoraMembresia:
    def calcular_vencimiento(self, fecha_inicio: date, duracion_dias: int) -> date:
        """RN-03: vencimiento = inicio + duración − 1 (el último día cuenta)."""
        return fecha_inicio + timedelta(days=duracion_dias - 1)

    def calcular_fecha_inicio(self, pagos: Iterable[Pago], hoy: date) -> date:
        """RN-04: si el socio renueva antes de vencer, no pierde los días que le quedan."""
        vencimiento_actual = self._vencimiento_actual(pagos)
        renueva_antes_de_vencer = vencimiento_actual is not None and vencimiento_actual >= hoy
        return vencimiento_actual + UN_DIA if renueva_antes_de_vencer else hoy

    def estado_de(self, pagos: Iterable[Pago], hoy: date) -> tuple[EstadoMembresia, date | None]:
        """RN-05: el estado no se almacena; se deriva de los pagos vigentes."""
        vencimiento_actual = self._vencimiento_actual(pagos)
        if vencimiento_actual is None:
            return EstadoMembresia.SIN_MEMBRESIA, None
        if hoy <= vencimiento_actual:
            return EstadoMembresia.ACTIVO, vencimiento_actual
        return EstadoMembresia.VENCIDO, vencimiento_actual

    def dias_de_mora(self, pagos: Iterable[Pago], hoy: date) -> int:
        estado, vencimiento = self.estado_de(pagos, hoy)
        if estado is not EstadoMembresia.VENCIDO or vencimiento is None:
            return 0
        return (hoy - vencimiento).days

    @staticmethod
    def _vencimiento_actual(pagos: Iterable[Pago]) -> date | None:
        vencimientos = [p.fecha_vencimiento for p in pagos if p.esta_vigente()]
        return max(vencimientos, default=None)
