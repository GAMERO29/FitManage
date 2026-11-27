"""Raíz del agregado «historial de pagos de un socio» (Software III, Guía 11).

Agrupa los pagos de un solo socio y protege como unidad dos invariantes:

- I-1 (RN-07): solo se anula el último pago vigente. «Último» = mayor fecha de inicio y, si
  empatan, el registrado más tarde.
- I-2 (RN-04): los periodos vigentes no se solapan. El siguiente pago inicia el día después del
  vencimiento más lejano, o hoy si el socio ya venció.

Lo que no protege: que una referencia no se repita entre pagos vigentes (RN-06) cruza socios, así
que no cabe en este agregado. La garantiza el índice único parcial de la base y el servicio solo
avisa antes. El bloqueo de la fila del socio (`bloquear_socio_*`) es el candado del agregado: dos
operaciones sobre el mismo socio no corren a la vez.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from dominio.calculadora import CalculadoraMembresia
from dominio.errores import PagoNoAnulable
from dominio.modelos import EstadoMembresia, Pago, Periodo, Socio


class HistorialPagos:
    def __init__(self, socio: Socio, pagos: Iterable[Pago]) -> None:
        self.socio = socio
        self._pagos = [p for p in pagos if p.socio.id == socio.id]
        self._calculadora = CalculadoraMembresia()

    @property
    def vigentes(self) -> list[Pago]:
        return [p for p in self._pagos if p.esta_vigente()]

    def ultimo_vigente(self) -> Pago | None:
        return max(self.vigentes, key=lambda p: (p.fecha_inicio, p.registrado_en), default=None)

    def exigir_que_sea_el_ultimo(self, pago: Pago) -> None:
        """I-1. Se llama antes de `Pago.anular`; el pago no sabe cuáles son sus hermanos."""
        if not pago.esta_vigente():
            raise PagoNoAnulable("El pago ya está anulado.")
        ultimo = self.ultimo_vigente()
        if ultimo is None or ultimo.id != pago.id:
            raise PagoNoAnulable("Solo se puede anular el último pago vigente del socio.")

    def periodo_del_siguiente(self, hoy: date, duracion_dias: int) -> Periodo:
        """I-2. RN-04 y RN-03 juntas: dónde empieza y dónde termina el próximo pago."""
        inicia = self._calculadora.calcular_fecha_inicio(self.vigentes, hoy)
        return Periodo.de_plan(inicia, duracion_dias)

    def estado(self, hoy: date) -> tuple[EstadoMembresia, date | None]:
        return self._calculadora.estado_de(self.vigentes, hoy)
