"""Las operaciones de pago de un mismo socio se hacen de una en una (Guía II-01, D-01 y D-02).

Registrar, anular y cambiar de plan leen los pagos vigentes del socio y escriben según lo que
leyeron. Si dos de esas operaciones se cruzan, las dos leen lo mismo: dos pagos simultáneos
empiezan el mismo día (rompe RN-04) y dos anulaciones del mismo pago responden las dos «anulado»
(rompe RN-07). Bloquear la fila del socio dentro de la transacción las pone en fila: la segunda
espera a que la primera confirme y después lee lo que quedó guardado.

Se llama desde los controladores, que son la frontera de la transacción. En SQLite no hace nada,
porque SQLite ya serializa todas las escrituras de la base.
"""

from __future__ import annotations

from uuid import UUID

from infraestructura.persistencia.models import PagoModelo, SocioModelo


def bloquear_socio_por_documento(tipo_documento: str, numero_documento: str) -> None:
    """Para registrar un pago: el socio llega por su documento."""
    list(
        SocioModelo.objects.select_for_update()
        .filter(tipo_documento=tipo_documento, numero_documento=numero_documento.strip())
        .values_list("id", flat=True)
    )


def bloquear_socio_del_pago(pago_id: UUID) -> None:
    """Para anular o cambiar de plan: el socio llega por uno de sus pagos."""
    socio_id = PagoModelo.objects.filter(id=pago_id).values_list("socio_id", flat=True).first()
    if socio_id is not None:
        list(
            SocioModelo.objects.select_for_update().filter(id=socio_id).values_list("id", flat=True)
        )
