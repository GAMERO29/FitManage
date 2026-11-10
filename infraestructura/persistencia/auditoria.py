"""Adaptador del puerto RegistroAuditoria (ADR N.° 19): una fila por evento en `auditoria`."""

from __future__ import annotations

from dominio.auditoria import EventoAuditoria
from infraestructura.persistencia.models import EventoAuditoriaModelo


class AuditoriaORM:
    """Inserta en la transacción abierta por el controlador; la base rechaza UPDATE y DELETE."""

    def registrar(self, evento: EventoAuditoria) -> None:
        EventoAuditoriaModelo.objects.create(
            ocurrido_en=evento.ocurrido_en,
            tipo=evento.tipo.value,
            actor_id=evento.actor.id if evento.actor else None,
            actor_nombre=evento.actor.nombre if evento.actor else "Sistema",
            entidad_id=evento.entidad_id,
            socio_id=evento.socio_id,
            detalle=evento.detalle,
        )
