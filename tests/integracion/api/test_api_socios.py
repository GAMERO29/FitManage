"""Socios: registro con autorización de datos (RF-01, PA-01)."""

import pytest

from infraestructura.persistencia.models import SocioModelo

NUEVO = {
    "tipoDocumento": "CE",
    "numeroDocumento": "4567890",
    "nombres": "Valentina",
    "apellidos": "Ruiz",
    "telefono": "3000000002",
    "autorizaTratamientoDatos": True,
}


@pytest.fixture
def recepcion(api):
    return api.como("laura@gimnasio-demo.co")


def test_registra_y_no_repite_documento_ni_telefono(recepcion):
    r = recepcion.post("/api/v1/socios", NUEVO)
    assert r.status_code == 201
    cuerpo = r.json()
    assert (cuerpo["nombreCorto"], cuerpo["documentoEnmascarado"]) == ("Valentina R.", "CE ***7890")
    assert cuerpo["estado"] == "SIN_MEMBRESIA"
    assert r["Location"] == "/api/v1/estados/CE/4567890"
    assert "3000000002" not in r.content.decode()
    assert SocioModelo.objects.filter(numero_documento="4567890").exists()


def test_documento_repetido_es_409(recepcion):
    """PA-01: no se crea un segundo registro."""
    r = recepcion.post(
        "/api/v1/socios", NUEVO | {"tipoDocumento": "CC", "numeroDocumento": "1090123456"}
    )
    assert r.status_code == 409 and r.json()["codigo"] == "DOCUMENTO_DUPLICADO"
    assert SocioModelo.objects.filter(numero_documento="1090123456").count() == 1


@pytest.mark.parametrize(
    "cambio",
    [{"autorizaTratamientoDatos": False}, {"telefono": "30000003"}, {"numeroDocumento": "12"}],
    ids=["sin-autorizacion", "telefono", "documento"],
)
def test_datos_que_el_contrato_rechaza(recepcion, cambio):
    assert recepcion.post("/api/v1/socios", NUEVO | cambio).status_code == 400
    assert not SocioModelo.objects.filter(numero_documento="4567890").exists()


def test_cedula_con_letras_la_rechaza_el_dominio(recepcion):
    """El contrato admite letras por el pasaporte; el dominio sabe que una CC es solo numérica."""
    r = recepcion.post(
        "/api/v1/socios", NUEVO | {"tipoDocumento": "CC", "numeroDocumento": "AB12345"}
    )
    assert r.status_code == 400


def test_el_entrenador_no_registra_socios(api):
    assert api.como("diego@gimnasio-demo.co").post("/api/v1/socios", NUEVO).status_code == 403
