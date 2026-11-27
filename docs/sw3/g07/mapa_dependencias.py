"""Software III · Guía 07: mapa de dependencias internas de FitManage, leído del código.

Recorre dominio/, aplicacion/ e infraestructura/ con el módulo ast (no ejecuta nada) y saca:
1. aristas módulo → módulo importado (solo internas, también las importaciones dentro de funciones);
2. ciclos entre paquetes (componentes fuertemente conexos de tamaño > 1);
3. nombres privados (_x) que un módulo importa de otro: dependen de un detalle que nadie publicó.
Uso:  python3 docs/sw3/g07/mapa_dependencias.py  [--aristas]
"""

import ast
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
CAPAS = ("dominio", "aplicacion", "infraestructura")


def modulos():
    for capa in CAPAS:
        for ruta in sorted((RAIZ / capa).rglob("*.py")):
            if "migrations" in ruta.parts:
                continue
            partes = ruta.relative_to(RAIZ).with_suffix("").parts
            yield ".".join(p for p in partes if p != "__init__"), ruta


def paquete(modulo):
    """dominio y aplicacion son un paquete cada uno; infraestructura se parte en sus hijos."""
    partes = modulo.split(".")
    return ".".join(partes[:2]) if partes[0] == "infraestructura" else partes[0]


def leer():
    conocidos = {nombre for nombre, _ in modulos()}
    aristas, privados = set(), []
    for nombre, ruta in modulos():
        for nodo in ast.walk(ast.parse(ruta.read_text(encoding="utf-8"))):
            if (
                isinstance(nodo, ast.ImportFrom)
                and nodo.module
                and nodo.module.split(".")[0] in CAPAS
            ):
                # "from infraestructura.api import tokens" depende de api.tokens, no del paquete.
                for a in nodo.names:
                    sub = f"{nodo.module}.{a.name}"
                    aristas.add((nombre, sub if sub in conocidos else nodo.module))
                privados += [
                    (nombre, nodo.module, a.name)
                    for a in nodo.names
                    if a.name.startswith("_") and not a.name.startswith("__")
                ]
            elif isinstance(nodo, ast.Import):
                aristas |= {(nombre, a.name) for a in nodo.names if a.name.split(".")[0] in CAPAS}
    return aristas, privados


def ciclos(aristas):
    """Tarjan sobre el grafo de paquetes; devuelve los componentes con más de un paquete."""
    grafo = defaultdict(set)
    for a, b in aristas:
        if paquete(a) != paquete(b):
            grafo[paquete(a)].add(paquete(b))
    indice, bajo, pila, en_pila, salida, n = {}, {}, [], set(), [], [0]

    def visitar(v):
        indice[v] = bajo[v] = n[0]
        n[0] += 1
        pila.append(v)
        en_pila.add(v)
        for w in sorted(grafo[v]):
            if w not in indice:
                visitar(w)
                bajo[v] = min(bajo[v], bajo[w])
            elif w in en_pila:
                bajo[v] = min(bajo[v], indice[w])
        if bajo[v] == indice[v]:
            comp = []
            while True:
                w = pila.pop()
                en_pila.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                salida.append(sorted(comp))

    for v in sorted(list(grafo)):
        if v not in indice:
            visitar(v)
    return salida, grafo


aristas, privados = leer()
componentes, grafo = ciclos(aristas)
print(f"Módulos: {len(list(modulos()))} · aristas internas: {len(aristas)}")
print("Dependencias entre paquetes:")
for origen in sorted(grafo):
    print(f"  {origen} → {', '.join(sorted(grafo[origen]))}")
print(f"Ciclos entre paquetes: {componentes or 'ninguno'}")
for comp in componentes:
    for a, b in sorted(aristas):
        if paquete(a) in comp and paquete(b) in comp and paquete(a) != paquete(b):
            print(f"  arista del ciclo: {a} → {b}")
print(f"Nombres privados importados desde otro módulo: {len(privados)}")
for origen, destino, nombre in privados:
    print(f"  {origen} importa {nombre} de {destino}")
if "--aristas" in sys.argv:
    for a, b in sorted(aristas):
        print(f"{a}\t{b}")
sys.exit(1 if componentes or privados else 0)
