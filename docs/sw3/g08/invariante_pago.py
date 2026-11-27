"""Software III · Guía 08: ¿puede existir un pago de 30 días que cubra 90? Se corre antes y después.

Uso:  python3 docs/sw3/g08/invariante_pago.py
"""

import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from dominio.errores import DatosInvalidos  # noqa: E402
from dominio.modelos import (  # noqa: E402
    ZONA_HORARIA,
    MedioPago,
    Pago,
    Rol,
    Socio,
    TipoDocumento,
    Usuario,
)

socia = Socio(
    TipoDocumento.CC,
    "1090000011",
    "Ana",
    "Prueba Demo",
    "3001234567",
    datetime(2026, 10, 1, 8, tzinfo=ZONA_HORARIA),
)
laura = Usuario("Laura Demo", "laura@demo.local", Rol.RECEPCIONISTA)
try:
    pago = Pago(
        socio=socia,
        plan_id=uuid4(),
        valor=Decimal("80000"),
        duracion_dias=30,
        medio=MedioPago.EFECTIVO,
        referencia=None,
        fecha_inicio=date(2026, 10, 7),
        fecha_vencimiento=date(2027, 1, 4),
        registrado_por=laura,
        registrado_en=datetime(2026, 10, 7, 18, 2, tzinfo=ZONA_HORARIA),
    )
    dias = (pago.fecha_vencimiento - pago.fecha_inicio).days + 1
    print(f"SE CREÓ: duración pagada 30 días, cobertura {dias} días (7 oct 2026 → 4 ene 2027)")
except DatosInvalidos as error:
    print(f"RECHAZADO: DatosInvalidos('{error}')")
