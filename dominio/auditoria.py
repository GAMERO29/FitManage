"""Eventos de auditoría (ADR N.° 19, DT-14): quién hizo qué, cuándo y qué cambió.

Un evento describe una operación que ya ocurrió y se guarda en la misma transacción que ella:
si la operación se revierte, el evento tampoco queda. No lleva el documento ni el teléfono del
socio: solo ids y valores del negocio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID

from dominio.modelos import Pago, Usuario, exigir_zona_horaria


class TipoEvento(Enum):
    PAGO_REGISTRADO = "PAGO_REGISTRADO"
    PAGO_ANULADO = "PAGO_ANULADO"
    PLAN_CAMBIADO = "PLAN_CAMBIADO"  # cambio de plan de un socio: anula y registra en un paso
    PRECIO_CAMBIADO = "PRECIO_CAMBIADO"
    PLAN_CREADO = "PLAN_CREADO"
    PLAN_DESACTIVADO = "PLAN_DESACTIVADO"
    PLAN_REACTIVADO = "PLAN_REACTIVADO"


Detalle = dict[str, str | int | None]


@dataclass(frozen=True)
class EventoAuditoria:
    tipo: TipoEvento
    actor: Usuario | None  # None: lo hizo el sistema (por ejemplo, un bloqueo automático)
    ocurrido_en: datetime
    entidad_id: UUID
    socio_id: UUID | None = None
    detalle: Detalle = field(default_factory=dict)

    def __post_init__(self) -> None:
        exigir_zona_horaria(self.ocurrido_en, "La fecha del evento")


def datos_del_pago(pago: Pago) -> Detalle:
    """Lo que identifica un pago en el rastro, sin datos personales del socio."""
    datos: Detalle = {
        "planId": str(pago.plan_id),
        "valor": int(pago.valor),
        "medio": pago.medio.value,
        "inicia": pago.fecha_inicio.isoformat(),
        "vence": pago.fecha_vencimiento.isoformat(),
        "registradoPor": pago.registrado_por.nombre,
        "registradoEl": pago.registrado_en.isoformat(timespec="seconds"),
    }
    if pago.referencia:
        datos["referencia"] = pago.referencia
    return datos
