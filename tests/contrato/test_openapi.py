"""El contrato OpenAPI cumple la regla de oro de la Guía 6.

1. Es un documento OpenAPI 3.0 válido.
2. Ningún endpoint queda sin esquema de seguridad declarado, y solo los tres
   que lo justifican lo anulan.
3. Ningún esquema de respuesta expone datos personales sin una razón de negocio.
4. Nivel 2 de Richardson: verbos con su semántica y códigos de estado coherentes.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename

CONTRATO = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.yaml"
VERBOS = ("get", "post", "put", "patch", "delete")
PUBLICOS = {"/salud get", "/auth/token post", "/auth/renovacion post"}
SENSIBLES = {"telefono", "numeroDocumento", "contrasena", "correo"}


@pytest.fixture(scope="module")
def spec() -> dict:
    documento, _ = read_from_filename(str(CONTRATO))
    return documento


def operaciones(spec: dict):
    for ruta, item in spec["paths"].items():
        for verbo in VERBOS:
            if verbo in item:
                yield ruta, verbo, item[verbo]


def resolver(spec: dict, nodo: dict) -> dict:
    while "$ref" in nodo:
        partes = nodo["$ref"].removeprefix("#/").split("/")
        nodo = spec
        for parte in partes:
            nodo = nodo[parte]
    return nodo


def propiedades(spec: dict, esquema: dict, vistos: set[str] | None = None) -> set[str]:
    """Todos los nombres de propiedad alcanzables desde un esquema."""
    vistos = vistos if vistos is not None else set()
    ref = esquema.get("$ref")
    if ref:
        if ref in vistos:
            return set()
        vistos.add(ref)
    esquema = resolver(spec, esquema)
    nombres = set(esquema.get("properties", {}))
    for hijo in esquema.get("properties", {}).values():
        nombres |= propiedades(spec, hijo, vistos)
    if "items" in esquema:
        nombres |= propiedades(spec, esquema["items"], vistos)
    return nombres


def test_es_openapi_3_valido(spec):
    assert spec["openapi"].startswith("3.0")
    validate(spec)


def test_hay_seguridad_global_jwt(spec):
    esquema = spec["components"]["securitySchemes"]["bearerAuth"]
    tipo = (esquema["type"], esquema["scheme"], esquema["bearerFormat"])
    assert tipo == ("http", "bearer", "JWT")
    assert spec["security"] == [{"bearerAuth": []}]


def test_solo_los_endpoints_justificados_anulan_el_jwt(spec):
    sin_bearer = {
        f"{ruta} {verbo}"
        for ruta, verbo, op in operaciones(spec)
        if "bearerAuth" not in {k for req in op.get("security", spec["security"]) for k in req}
    }
    assert sin_bearer == PUBLICOS


def test_toda_operacion_protegida_documenta_el_401(spec):
    for ruta, verbo, op in operaciones(spec):
        if f"{ruta} {verbo}" not in {"/salud get", "/auth/token post"}:
            assert "401" in op["responses"], f"{verbo.upper()} {ruta}"


def test_las_operaciones_de_administrador_documentan_el_403(spec):
    for ruta, verbo in (("/reportes/ingresos", "get"), ("/pagos/{pagoId}", "patch")):
        assert "403" in spec["paths"][ruta][verbo]["responses"]


def test_ningun_get_lleva_cuerpo(spec):
    for ruta, verbo, op in operaciones(spec):
        if verbo == "get":
            assert "requestBody" not in op, ruta


def test_los_post_que_crean_responden_201(spec):
    for ruta in ("/socios", "/pagos"):
        respuestas = spec["paths"][ruta]["post"]["responses"]
        assert "201" in respuestas
        assert "Location" in respuestas["201"]["headers"]


def test_la_anulacion_es_patch_y_no_delete(spec):
    pago = spec["paths"]["/pagos/{pagoId}"]
    assert "patch" in pago and "delete" not in pago and "post" not in pago


def test_el_estado_publico_no_expone_datos_sensibles(spec):
    for nombre in ("EstadoPublico", "ListaEstados", "SocioRegistrado", "Pago", "ReporteIngresos"):
        expuestas = propiedades(spec, {"$ref": f"#/components/schemas/{nombre}"})
        assert not expuestas & SENSIBLES, f"{nombre}: {expuestas & SENSIBLES}"


def test_el_unico_telefono_expuesto_es_el_de_los_recordatorios(spec):
    con_telefono = []
    for ruta, verbo, op in operaciones(spec):
        for codigo, respuesta in op["responses"].items():
            respuesta = resolver(spec, respuesta)
            for contenido in respuesta.get("content", {}).values():
                if "telefono" in propiedades(spec, contenido["schema"]):
                    con_telefono.append(f"{verbo.upper()} {ruta} {codigo}")
    assert con_telefono == ["GET /vencimientos 200"]


def test_la_contrasena_nunca_se_devuelve(spec):
    credenciales = spec["components"]["schemas"]["Credenciales"]["properties"]["contrasena"]
    assert credenciales["writeOnly"] is True
