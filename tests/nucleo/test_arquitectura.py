"""Regla de dependencia de la arquitectura hexagonal (ADR N.° 04), comprobada en cada push."""

import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
PROHIBIDOS = {
    "dominio": (
        "django",
        "psycopg",
        "sqlalchemy",
        "requests",
        "infraestructura",
        "aplicacion",
        "config",
    ),
    "aplicacion": ("django", "psycopg", "sqlalchemy", "requests", "infraestructura", "config"),
}


def _importaciones(archivo: Path) -> set[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    nombres: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            nombres.add(nodo.module)
    return nombres


@pytest.mark.parametrize("paquete", sorted(PROHIBIDOS))
def test_el_nucleo_no_importa_infraestructura(paquete):
    fugas = [
        f"{archivo.relative_to(RAIZ)} importa {nombre}"
        for archivo in sorted((RAIZ / paquete).rglob("*.py"))
        for nombre in _importaciones(archivo)
        if nombre.split(".")[0] in PROHIBIDOS[paquete]
    ]
    assert fugas == []
