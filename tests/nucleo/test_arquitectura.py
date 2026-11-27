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


# Guía 15 (DT-16): los controladores traducen HTTP y llaman a un caso de uso. No calculan estados ni
# usan repositorios directamente; para eso están `aplicacion/` y la raíz de composición.
PROHIBIDOS_EN_CONTROLADORES = ("dominio.calculadora", "infraestructura.persistencia.repositorios")


def test_los_controladores_no_hacen_el_trabajo_de_los_casos_de_uso():
    vistas = RAIZ / "infraestructura" / "api" / "vistas.py"
    fugas = sorted(n for n in _importaciones(vistas) if n in PROHIBIDOS_EN_CONTROLADORES)
    assert fugas == []


# Software III, Guía 05: la regla anterior miraba módulos y dejó pasar `PlanModelo`, importado desde
# `infraestructura.persistencia.models`: la vista consultaba el ORM y decidía qué planes ver. Ahora
# se revisan los nombres. La única excepción es la tabla de idempotencia, que es un detalle del
# protocolo HTTP (la cabecera Idempotency-Key), no del negocio.
MODELOS_PERMITIDOS_EN_CONTROLADORES = {"IdempotenciaModelo"}


def test_los_controladores_no_consultan_modelos_del_orm():
    vistas = RAIZ / "infraestructura" / "api" / "vistas.py"
    importados = {
        alias.name
        for nodo in ast.walk(ast.parse(vistas.read_text(encoding="utf-8")))
        if isinstance(nodo, ast.ImportFrom) and nodo.module == "infraestructura.persistencia.models"
        for alias in nodo.names
    }
    assert importados - MODELOS_PERMITIDOS_EN_CONTROLADORES == set()


# Guía II-01 (D-01, D-02) y II-03: todo controlador que escribe pagos bloquea al socio y abre una
# transacción, para que el evento de auditoría y la operación queden juntos o no queden.
ESCRIBEN_PAGOS = {"registro_pago", "anulacion_pago", "cambio_plan"}


def _llamadas(funcion: ast.FunctionDef) -> set[str]:
    nombres = set()
    for nodo in ast.walk(funcion):
        if isinstance(nodo, ast.Call):
            f = nodo.func
            nombres.add(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", ""))
    return nombres


def test_toda_escritura_de_pagos_bloquea_al_socio_dentro_de_una_transaccion():
    arbol = ast.parse((RAIZ / "infraestructura" / "api" / "vistas.py").read_text(encoding="utf-8"))
    revisadas, fugas = 0, []
    for funcion in (n for n in arbol.body if isinstance(n, ast.FunctionDef)):
        llamadas = _llamadas(funcion)
        servicios = llamadas & ESCRIBEN_PAGOS
        if not servicios or funcion.name.startswith("vista_previa"):  # la vista previa solo lee
            continue
        revisadas += 1
        if "atomic" not in llamadas or not any(n.startswith("bloquear_socio") for n in llamadas):
            fugas.append(funcion.name)
    assert revisadas >= 3 and fugas == []


# Software III, Guía 07. Dos reglas que antes nadie revisaba:
# 1) Ningún módulo importa un nombre privado (_x) de otro. autenticacion.py y consultas.py usaban
#    `_a_usuario`, `_a_pago` y `_a_socio` de repositorios.py; ahora viven en persistencia/mapeo.py.
# 2) Los paquetes de infraestructura no forman ciclos. consultas.py importaba de api/presentacion.py
#    mientras api/vistas.py importaba consultas.py; la máscara del documento pasó a dominio/.
def _modulos() -> dict[str, Path]:
    salida = {}
    for capa in ("dominio", "aplicacion", "infraestructura"):
        for archivo in (RAIZ / capa).rglob("*.py"):
            if "migrations" not in archivo.parts:
                partes = archivo.relative_to(RAIZ).with_suffix("").parts
                salida[".".join(p for p in partes if p != "__init__")] = archivo
    return salida


def _desde(archivo: Path):
    for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            yield nodo.module, [alias.name for alias in nodo.names]


def test_ningun_modulo_importa_nombres_privados_de_otro():
    fugas = [
        f"{nombre} importa {n} de {origen}"
        for nombre, archivo in _modulos().items()
        for origen, nombres in _desde(archivo)
        for n in nombres
        if n.startswith("_") and not n.startswith("__") and origen != "__future__"
    ]
    assert fugas == []


def test_los_paquetes_de_infraestructura_no_forman_ciclos():
    modulos = _modulos()

    def paquete(m: str) -> str:
        partes = m.split(".")
        return ".".join(partes[:2]) if partes[0] == "infraestructura" else partes[0]

    grafo: dict[str, set[str]] = {}
    for nombre, archivo in modulos.items():
        for origen, nombres in _desde(archivo):
            destinos = {f"{origen}.{n}" if f"{origen}.{n}" in modulos else origen for n in nombres}
            for d in destinos:
                if d in modulos and paquete(d) != paquete(nombre):
                    grafo.setdefault(paquete(nombre), set()).add(paquete(d))

    def alcanza(desde: str, hasta: str, vistos: set[str]) -> bool:
        for siguiente in grafo.get(desde, ()):
            if siguiente == hasta or (
                siguiente not in vistos and alcanza(siguiente, hasta, vistos | {siguiente})
            ):
                return True
        return False

    ciclos = sorted(p for p in grafo if alcanza(p, p, {p}))
    assert ciclos == []


# Software III, Guía 08: el estado de un pago o de un plan cambia solo con sus métodos (anular,
# desactivar), que revisan la transición. Fuera del dominio nadie asigna esos atributos.
ATRIBUTOS_DE_ESTADO = {
    "estado",
    "fecha_anulacion",
    "anulado_por",
    "motivo_anulacion",
    "activo",
    "fecha_inicio",
    "fecha_vencimiento",
}


def test_fuera_del_dominio_nadie_cambia_el_estado_asignando_atributos():
    fugas = []
    for capa in ("aplicacion", "infraestructura"):
        for archivo in sorted((RAIZ / capa).rglob("*.py")):
            for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
                if isinstance(nodo, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                    destinos = nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]
                    for d in destinos:
                        for hoja in ast.walk(d):
                            if isinstance(hoja, ast.Attribute) and hoja.attr in ATRIBUTOS_DE_ESTADO:
                                fugas.append(
                                    f"{archivo.relative_to(RAIZ)}:{nodo.lineno} .{hoja.attr}"
                                )
    assert fugas == []
