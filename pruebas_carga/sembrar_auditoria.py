"""Guía II-04 · 30.000 eventos de auditoría ficticios en 31 días, para la carga de la consulta.

Uso: DATABASE_URL=... python pruebas_carga/sembrar_auditoria.py (después de sembrar.py y migrate).
Nunca contra producción: solo acepta bases en localhost o 127.0.0.1.
"""

from __future__ import annotations

import os
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from dominio.modelos import ZONA_HORARIA  # noqa: E402
from infraestructura.persistencia.models import (  # noqa: E402
    EventoAuditoriaModelo,
    SocioModelo,
    UsuarioModelo,
)

EVENTOS = 30_000
FIN = datetime(2026, 11, 10, 20, 0, tzinfo=ZONA_HORARIA)
TIPOS = ["PAGO_REGISTRADO"] * 8 + ["PAGO_ANULADO", "PLAN_CAMBIADO"]


def main() -> None:
    if urlparse(os.environ.get("DATABASE_URL", "")).hostname not in ("localhost", "127.0.0.1"):
        sys.exit("Solo bases locales de carga. Nunca producción.")
    azar = random.Random(2026)
    actor = UsuarioModelo.objects.first()
    socios = list(SocioModelo.objects.values_list("id", flat=True)[:2000])
    filas = [
        EventoAuditoriaModelo(
            ocurrido_en=FIN - timedelta(minutes=azar.randint(0, 31 * 24 * 60)),
            tipo=azar.choice(TIPOS),
            actor=actor,
            actor_nombre=actor.nombre,
            entidad_id=uuid.uuid4(),
            socio_id=azar.choice(socios),
            detalle={"valor": 75000, "plan": "Mensual", "medio": "EFECTIVO", "motivo": "Carga"},
        )
        for _ in range(EVENTOS)
    ]
    EventoAuditoriaModelo.objects.bulk_create(filas, batch_size=2_000)
    print(f"Sembrados {EventoAuditoriaModelo.objects.count()} eventos de auditoría.")


if __name__ == "__main__":
    main()
