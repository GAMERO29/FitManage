"""Reglas del contexto Acceso del personal (RF-09)."""

from __future__ import annotations

from datetime import datetime, timedelta

from dominio.modelos import exigir_zona_horaria

MAXIMO_INTENTOS = 5
DURACION_BLOQUEO = timedelta(minutes=15)


class PoliticaBloqueo:
    """Tras 5 intentos fallidos la cuenta se bloquea 15 minutos y luego se libera sola (PA-10)."""

    def registrar_fallo(
        self, intentos_previos: int, ahora: datetime
    ) -> tuple[int, datetime | None]:
        exigir_zona_horaria(ahora, "La hora del intento")
        intentos = intentos_previos + 1
        if intentos >= MAXIMO_INTENTOS:
            return intentos, ahora + DURACION_BLOQUEO
        return intentos, None

    @staticmethod
    def esta_bloqueada(bloqueada_hasta: datetime | None, ahora: datetime) -> bool:
        return bloqueada_hasta is not None and ahora < bloqueada_hasta

    def segundos_restantes(self, bloqueada_hasta: datetime | None, ahora: datetime) -> int:
        if not self.esta_bloqueada(bloqueada_hasta, ahora):
            return 0
        return int((bloqueada_hasta - ahora).total_seconds())
