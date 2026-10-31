"""Reloj del negocio: implementa el puerto Reloj en la zona America/Bogota (paga DT-07)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime

from dominio.modelos import ZONA_HORARIA


def _ahora_utc() -> datetime:
    return datetime.now(UTC)


class RelojBogota:
    """El servidor puede estar en UTC; el negocio siempre vive en hora de Colombia."""

    def __init__(self, ahora_utc: Callable[[], datetime] = _ahora_utc) -> None:
        self._ahora_utc = ahora_utc

    def ahora(self) -> datetime:
        return self._ahora_utc().astimezone(ZONA_HORARIA)

    def hoy(self) -> date:
        return self.ahora().date()
