"""Software III · Guía 13: la regla de la IA contra los casos del catálogo (RF-10 v1.3).

Uso:  python3 docs/sw3/g13/verificar_propuesta.py
"""

import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from propuesta_ia import puede_anular  # noqa: E402

from dominio.especificaciones import PUEDE_ANULAR, SolicitudAnulacion  # noqa: E402
from dominio.modelos import ZONA_HORARIA, Rol, Usuario  # noqa: E402


@dataclass
class P:
    registrado_por: Usuario
    registrado_en: datetime


laura = Usuario("Laura Demo", "laura.a@demo.local", Rol.RECEPCIONISTA)
otra = Usuario("Laura Demo", "laura.b@demo.local", Rol.RECEPCIONISTA)
carlos = Usuario("Carlos Demo", "carlos@demo.local", Rol.ADMINISTRADOR)


class U:  # la IA compara usuario.rol con un texto
    def __init__(self, u):
        self.nombre, self.rol, self.id = u.nombre, u.rol.value, u.id


hoy = datetime.now(ZONA_HORARIA).date()
noche = datetime.combine(hoy, datetime.min.time(), ZONA_HORARIA).replace(hour=20)  # 8 p. m. Bogotá
ayer_noche = noche - timedelta(days=1)
casos = [
    ("Laura, su pago de hoy a las 8 p. m.", P(laura, noche.astimezone(UTC)), laura, True),
    (
        "Laura, su pago de ayer a las 8 p. m.",
        P(laura, ayer_noche.astimezone(UTC)),
        laura,
        False,
    ),
    ("Otra Laura (mismo nombre), pago de Laura hoy", P(laura, noche), otra, False),
    ("Administrador, pago de ayer", P(laura, ayer_noche), carlos, True),
]
fallas = 0
for nombre, pago, usuario, esperado in casos:
    ia = puede_anular(pago, U(usuario))
    fm = PUEDE_ANULAR.es_satisfecha_por(SolicitudAnulacion(pago, usuario, hoy))
    fallas += ia != esperado
    marca = "PASA " if ia == esperado else "FALLA"
    print(f"{marca} IA {nombre}: {ia} (esperado {esperado}) · FitManage: {fm}")
print(f"\nLa IA falla {fallas} de {len(casos)} casos.")
