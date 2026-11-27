"""Software III, Guía 10: la matriz de diseño trazable no puede apuntar a algo que no existe.

Lee docs/sw3/g10/matriz.md y comprueba, para cada fila, que el componente exista, que la operación
esté en el contrato y que cada prueba citada esté definida en su archivo. Si alguien renombra una
prueba o borra una operación, la matriz deja de pasar y hay que actualizarla en el mismo PR.
"""

import ast
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
MATRIZ = RAIZ / "docs" / "sw3" / "g10" / "matriz.md"


def filas():
    for linea in MATRIZ.read_text(encoding="utf-8").splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) == 4 and celdas[0].startswith(("RF-", "RNF-", "RN-")):
            yield celdas


def pruebas_definidas(archivo: Path) -> set[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    return {n.name for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)}


def test_la_matriz_tiene_al_menos_tres_requisitos_distintos():
    requisitos = {f[0].split(" ")[0] for f in filas()}
    assert len(requisitos) >= 3, requisitos


@pytest.mark.parametrize(
    "fila", list(filas()), ids=[f"{i:02d}-{f[0].split()[0]}" for i, f in enumerate(filas(), 1)]
)
def test_cada_fila_apunta_a_algo_que_existe(fila):
    requisito, componente, operacion, pruebas = fila
    assert (RAIZ / componente.strip("`")).is_file(), f"{requisito}: no existe {componente}"
    contrato = (RAIZ / "docs" / "api" / "openapi.yaml").read_text(encoding="utf-8")
    assert f"operationId: {operacion}\n" in contrato, (
        f"{requisito}: el contrato no tiene {operacion}"
    )
    citas = re.findall(r"`([^`]+)::([^`]+)`", pruebas)
    assert citas, f"{requisito}: la fila no cita ninguna prueba"
    for archivo, nombre in citas:
        assert nombre in pruebas_definidas(RAIZ / archivo), (
            f"{requisito}: falta {archivo}::{nombre}"
        )
