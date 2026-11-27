"""Software III · Guía 08: la propuesta de la IA contra las tres reglas que FitManage ya prueba.

Uso:  python3 docs/sw3/g08/verificar_propuesta.py
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from propuesta_ia import Membresia  # noqa: E402

from dominio.modelos import Periodo  # noqa: E402


def revisar(nombre, ok, detalle):
    print(f"{'PASA ' if ok else 'FALLA'} {nombre}: {detalle}")


# RN-03: 30 días desde el 7 de octubre vencen el 5 de noviembre (el último día cuenta).
ia = Membresia("1090000011", date(2026, 10, 7), 30)
revisar("IA, RN-03", ia.fecha_vencimiento == date(2026, 11, 5), f"vence {ia.fecha_vencimiento}")
revisar("IA, 6 nov ya vencida", not ia.esta_activa(date(2026, 11, 6)), "entra el 6 de noviembre")
fm = Periodo.de_plan(date(2026, 10, 7), 30)
revisar("FitManage, RN-03", fm.vence == date(2026, 11, 5), f"vence {fm.vence}")
revisar("FitManage, 6 nov ya vencida", not fm.cubre(date(2026, 11, 6)), "no entra el 6")

# RN-05 y RN-07: el estado sale de los pagos vigentes y solo cambia con una operación que revisa
# la transición. El setter de la IA acepta cualquier texto y no sabe de pagos.
m = Membresia("1090000011", date(2026, 10, 7), 30)
try:
    m.set_estado("ACTIVA-PREMIUM")
    revisar("IA, transición validada", False, f"set_estado aceptó {m.estado!r}")
except ValueError:
    revisar("IA, transición validada", True, "rechazó un estado inventado")
m.set_estado("ACTIVA")
revisar(
    "IA, RN-05",
    False,
    "esta_activa(7 oct) = "
    f"{m.esta_activa(date(2026, 10, 7))} aunque nada dice si el pago sigue vigente o se anuló",
)
