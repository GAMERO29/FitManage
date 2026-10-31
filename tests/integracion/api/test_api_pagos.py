"""Membresías y cobros: el pago y la anulación pasan por el dominio y se guardan de verdad."""

import uuid

import pytest
from apoyo_api import ID_MENSUAL, ID_PAGO_JORGE

from infraestructura.persistencia.models import IdempotenciaModelo, PagoModelo

PAGOS = "/api/v1/pagos"


def clave() -> dict:
    return {"Idempotency-Key": str(uuid.uuid4())}


def pago_de(
    documento="1090123456", medio="NEQUI", referencia="M654321", plan=ID_MENSUAL, tipo="CC"
):
    cuerpo = {
        "tipoDocumento": tipo,
        "numeroDocumento": documento,
        "planId": str(plan),
        "medio": medio,
    }
    if referencia:
        cuerpo["referencia"] = referencia
    return cuerpo


@pytest.fixture
def recepcion(api):
    return api.como("laura@gimnasio-demo.co")


def test_renovacion_anticipada_no_pierde_dias(recepcion):
    """RN-04: Ana está activa hasta el 21/10; el plan nuevo empieza el 22/10."""
    r = recepcion.post(PAGOS, pago_de(), clave())
    assert r.status_code == 201
    cuerpo = r.json()
    assert (cuerpo["inicia"], cuerpo["vence"], cuerpo["valor"]) == (
        "2026-10-22",
        "2026-11-20",
        75000,
    )
    assert (cuerpo["plan"], cuerpo["registradoPor"], cuerpo["estado"]) == (
        "Mensual",
        "Laura",
        "VIGENTE",
    )
    assert r["Location"] == f"{PAGOS}/{cuerpo['id']}"
    assert PagoModelo.objects.filter(id=cuerpo["id"], referencia="M654321").exists()


def test_socio_vencido_empieza_hoy(recepcion, gimnasio):
    cuerpo = recepcion.post(
        PAGOS, pago_de("1093445566", "EFECTIVO", None, gimnasio["trimestral"].id), clave()
    ).json()
    assert (cuerpo["inicia"], cuerpo["vence"]) == ("2026-10-07", "2027-01-04")
    assert "referencia" not in cuerpo


def test_nequi_sin_referencia_es_400(recepcion):
    r = recepcion.post(PAGOS, pago_de(referencia=None), clave())
    assert r.status_code == 400 and r.json()["codigo"] == "SOLICITUD_INVALIDA"


def test_comprobante_duplicado_es_409_y_no_se_guarda(recepcion):
    antes = PagoModelo.objects.count()
    r = recepcion.post(PAGOS, pago_de(referencia="M123456"), clave())
    assert r.status_code == 409 and r.json()["codigo"] == "COMPROBANTE_DUPLICADO"
    assert PagoModelo.objects.count() == antes
    assert not IdempotenciaModelo.objects.exists()  # un error no queda guardado como respuesta


@pytest.mark.parametrize(
    "cuerpo",
    [pago_de(documento="1111111111"), pago_de(plan=uuid.uuid4())],
    ids=["socio", "plan"],
)
def test_socio_o_plan_inexistente_es_404(recepcion, cuerpo):
    assert recepcion.post(PAGOS, cuerpo, clave()).status_code == 404


def test_el_cliente_no_puede_mandar_fechas_ni_valor(recepcion):
    r = recepcion.post(PAGOS, pago_de() | {"valor": 8000, "inicia": "2026-01-01"}, clave())
    assert r.status_code == 400
    assert PagoModelo.objects.count() == 2


def test_sin_idempotency_key_es_400(recepcion):
    assert recepcion.post(PAGOS, pago_de()).status_code == 400


def test_doble_clic_con_la_misma_clave_crea_un_solo_pago(recepcion):
    """PA-11: el segundo envío devuelve la misma respuesta y no crea otro pago."""
    misma = clave()
    primera = recepcion.post(PAGOS, pago_de(), misma)
    segunda = recepcion.post(PAGOS, pago_de(), misma)
    assert (primera.status_code, segunda.status_code) == (201, 201)
    assert primera.json() == segunda.json() and segunda["Idempotent-Replayed"] == "true"
    assert PagoModelo.objects.count() == 3


def test_el_entrenador_no_registra_pagos(api):
    r = api.como("diego@gimnasio-demo.co").post(PAGOS, pago_de(), clave())
    assert r.status_code == 403 and r.json()["codigo"] == "SIN_PERMISO"


@pytest.fixture
def administracion(api):
    return api.como("carlos@gimnasio-demo.co")


ANULACION = {"estado": "ANULADO", "motivo": "Se registró Mensual y el socio pagó Quincenal"}


def test_anular_el_ultimo_pago_recalcula_la_membresia(administracion):
    """PA-08: el pago queda anulado (no se borra) y el socio pasa a sin membresía."""
    r = administracion.patch(f"{PAGOS}/{ID_PAGO_JORGE}", ANULACION)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["estado"] == "ANULADO"
    assert cuerpo["anulacion"]["anuladoPor"] == "Carlos"
    assert PagoModelo.objects.get(id=ID_PAGO_JORGE).estado == "ANULADO"
    estado = administracion.get("/api/v1/estados/CC/1093445566").json()
    assert estado["estado"] == "SIN_MEMBRESIA"


def test_la_referencia_de_un_pago_anulado_se_puede_volver_a_usar(administracion):
    """PA-09."""
    administracion.patch(f"{PAGOS}/{ID_PAGO_JORGE}", ANULACION)
    r = administracion.post(PAGOS, pago_de("1093445566", referencia="M123456"), clave())
    assert r.status_code == 201


def test_no_se_anula_un_pago_que_no_es_el_ultimo(administracion):
    nuevo = administracion.post(PAGOS, pago_de(), clave()).json()
    anterior = (
        PagoModelo.objects.filter(socio__numero_documento="1090123456")
        .exclude(id=nuevo["id"])
        .get()
    )
    r = administracion.patch(f"{PAGOS}/{anterior.id}", ANULACION)
    assert r.status_code == 409 and r.json()["codigo"] == "NO_ES_EL_ULTIMO_PAGO"


def test_un_pago_ya_anulado_responde_409(administracion):
    administracion.patch(f"{PAGOS}/{ID_PAGO_JORGE}", ANULACION)
    assert administracion.patch(f"{PAGOS}/{ID_PAGO_JORGE}", ANULACION).status_code == 409


def test_anular_un_pago_inexistente_es_404(administracion):
    assert administracion.patch(f"{PAGOS}/{uuid.uuid4()}", ANULACION).status_code == 404


def test_motivo_demasiado_corto_es_400(administracion):
    assert (
        administracion.patch(
            f"{PAGOS}/{ID_PAGO_JORGE}", {"estado": "ANULADO", "motivo": "x"}
        ).status_code
        == 400
    )


def test_la_recepcionista_no_puede_anular(api):
    """PA-07."""
    r = api.como("laura@gimnasio-demo.co").patch(f"{PAGOS}/{ID_PAGO_JORGE}", ANULACION)
    assert r.status_code == 403
    assert PagoModelo.objects.get(id=ID_PAGO_JORGE).estado == "VIGENTE"


def test_delete_no_existe_sobre_pagos(administracion, client):
    r = client.delete(
        f"{PAGOS}/{ID_PAGO_JORGE}", HTTP_AUTHORIZATION=f"Bearer {administracion.token}"
    )
    assert r.status_code == 405
