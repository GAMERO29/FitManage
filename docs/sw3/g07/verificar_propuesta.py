"""Software III · Guía 07: la cláusula del correo, probada contra el doble que propuso la IA.

El adaptador real busca con correo__iexact y la prueba de integración
tests/integracion/api/test_api_acceso.py::test_el_correo_no_distingue_mayusculas lo exige.
Un doble que no respete eso daría pruebas verdes con un comportamiento distinto al de producción.
Uso:  python3 docs/sw3/g07/verificar_propuesta.py
"""

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from propuesta_ia import CuentasEnMemoria  # noqa: E402


@dataclass
class Cuenta:
    correo: str
    clave_hash: str = "pbkdf2_sha256$..."


class CuentasEnMemoriaCorregido(CuentasEnMemoria):
    """Corrección: la llave es el correo en minúsculas, igual que la comparación de la base."""

    def __init__(self, *cuentas) -> None:
        self._cuentas = {c.correo.casefold(): c for c in cuentas}

    def por_correo(self, correo: str):
        return self._cuentas.get(correo.casefold())

    def guardar(self, cuenta) -> None:
        self._cuentas[cuenta.correo.casefold()] = cuenta


fallas = 0
for nombre, clase in (
    ("doble de la IA", CuentasEnMemoria),
    ("doble corregido", CuentasEnMemoriaCorregido),
):
    repo = clase(Cuenta("laura@gimnasio-demo.co"))
    encontrada = repo.por_correo("Laura@Gimnasio-Demo.co") is not None
    print(
        f"{'PASA ' if encontrada else 'FALLA'} {nombre}: "
        f"'Laura@Gimnasio-Demo.co' encuentra la cuenta = {encontrada}"
    )
    fallas += 0 if encontrada or clase is CuentasEnMemoria else 1
# El doble de la IA debe fallar (es el hallazgo); el corregido debe pasar.
sys.exit(fallas)
