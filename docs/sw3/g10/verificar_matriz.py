"""Software III · Guía 10: revisa cualquier matriz con el mismo criterio de test_trazabilidad.py.

Uso:  python3 docs/sw3/g10/verificar_matriz.py docs/sw3/g10/matriz_ia.md
"""

import ast
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
CONTRATO = (RAIZ / "docs" / "api" / "openapi.yaml").read_text(encoding="utf-8")
fallas = 0


def definidas(archivo: Path) -> set[str]:
    if not archivo.is_file():
        return set()
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    return {n.name for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)}


for linea in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
    if len(celdas) != 4 or not celdas[0].startswith(("RF-", "RNF-")):
        continue
    req, componente, operacion, pruebas = celdas
    revisiones = [
        (f"componente {componente}", (RAIZ / componente.strip("`")).is_file()),
        (f"operación {operacion}", f"operationId: {operacion}\n" in CONTRATO),
    ]
    for archivo, nombre in re.findall(r"`([^`]+)::([^`]+)`", pruebas):
        revisiones.append((f"prueba {nombre}", nombre in definidas(RAIZ / archivo)))
    for que, ok in revisiones:
        fallas += 0 if ok else 1
        print(f"{'PASA ' if ok else 'FALLA'} {req}: {que}")
print(f"\n{fallas} referencias que no existen")
sys.exit(1 if fallas else 0)
