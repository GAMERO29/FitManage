"""Siembra la base del entorno de carga con el volumen de QA-01: 2.000 socios y 20.000 pagos.

Uso (solo contra una base local cuyo nombre termine en _carga):
    DATABASE_URL=postgresql://fitmanage:CLAVE@127.0.0.1:5432/fitmanage_carga \\
        python pruebas_carga/sembrar.py

Se niega a correr contra cualquier otra base: este script borra y vuelve a crear los datos.
"""

from __future__ import annotations

import os
import random
import sys
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# "db" es el nombre del servicio de PostgreSQL dentro de docker compose (Guía 13): nunca producción.
HOSTS_PERMITIDOS = {"127.0.0.1", "localhost", "db"}
SOCIOS = 2_000
PAGOS = 20_000
HOY = date(2026, 11, 2)
CLAVE_RECEPCION = os.environ.get("CLAVE_CARGA", "carga-local-2026")


def revisar_destino(url: str | None) -> None:
    partes = urlparse(url or "")
    if partes.hostname not in HOSTS_PERMITIDOS or not partes.path.endswith("_carga"):
        sys.exit(
            "Me niego a sembrar: DATABASE_URL debe apuntar a una base local terminada en _carga "
            f"(recibí host={partes.hostname!r}, base={partes.path.lstrip('/')!r})."
        )


def main() -> None:
    revisar_destino(os.environ.get("DATABASE_URL"))

    import django

    django.setup()
    from django.contrib.auth.hashers import make_password
    from django.core.management import call_command
    from django.db import transaction

    from dominio.modelos import ZONA_HORARIA
    from infraestructura.persistencia.models import (
        PagoModelo,
        PlanModelo,
        SocioModelo,
        UsuarioModelo,
    )

    call_command("migrate", verbosity=0)
    azar = random.Random(2026)  # siempre los mismos datos, para comparar corridas
    with transaction.atomic():
        for modelo in (PagoModelo, PlanModelo, SocioModelo, UsuarioModelo):
            modelo.objects.all().delete()
        laura = UsuarioModelo.objects.create(
            nombre="Laura",
            correo="laura@carga.local",
            rol="RECEPCIONISTA",
            clave_hash=make_password(CLAVE_RECEPCION),
        )
        planes = [
            PlanModelo.objects.create(nombre=n, duracion_dias=d, precio=Decimal(p))
            for n, d, p in (
                ("Diario", 1, 8000),
                ("Quincenal", 15, 45000),
                ("Mensual", 30, 75000),
                ("Trimestral", 90, 200000),
            )
        ]
        socios = [
            SocioModelo(
                tipo_documento="CC",
                numero_documento=str(1_090_000_000 + i),
                nombres=azar.choice(["Ana", "Luis", "María", "Jorge", "Paula", "Andrés"]),
                apellidos=azar.choice(["Pérez", "Rincón", "Gil", "Suárez", "Mora", "Ortiz"]),
                telefono=f"300{i:07d}",
                autorizacion_datos=datetime(2026, 1, 10, 9, 0, tzinfo=ZONA_HORARIA),
            )
            for i in range(SOCIOS)
        ]
        SocioModelo.objects.bulk_create(socios)
        pagos = []
        for n in range(PAGOS):
            socio = socios[n % SOCIOS]  # 10 pagos por socio: un año de renovaciones
            plan = azar.choices(planes, weights=[1, 2, 6, 1])[0]
            inicio = HOY - timedelta(days=azar.randint(0, 360))
            pagos.append(
                PagoModelo(
                    id=uuid.uuid4(),
                    socio=socio,
                    plan=plan,
                    valor=plan.precio,
                    duracion_dias=plan.duracion_dias,
                    medio="EFECTIVO",
                    referencia=None,
                    fecha_inicio=inicio,
                    fecha_vencimiento=inicio + timedelta(days=plan.duracion_dias - 1),
                    registrado_por=laura,
                    registrado_en=datetime.combine(inicio, datetime.min.time(), ZONA_HORARIA),
                    estado="ANULADO" if azar.random() < 0.02 else "VIGENTE",
                )
            )
        PagoModelo.objects.bulk_create(pagos, batch_size=2_000)
    print(f"Sembrados {SocioModelo.objects.count()} socios y {PagoModelo.objects.count()} pagos.")


if __name__ == "__main__":
    main()
