"""Cambiar el plan de un socio en un solo paso: anula el último pago y registra el nuevo.

El plan nuevo empieza el mismo día que el pago que reemplaza y cuesta su precio completo (RN-08);
si el pago nuevo no se puede registrar, la anulación tampoco queda.
"""

import pytest
from apoyo_api import ID_MENSUAL, ID_PAGO_JORGE, ClienteAPI
from django.test import Client

from infraestructura.persistencia.models import PagoModelo


@pytest.fixture
def administracion(api):
    return api.como("carlos@gimnasio-demo.co")


@pytest.fixture
def trimestral(administracion):
    return next(
        p for p in administracion.get("/api/v1/planes").json() if p["nombre"] == "Trimestral"
    )


@pytest.fixture
def pago_de_ana(administracion):
    return administracion.get("/api/v1/socios/CC/1090123456/pagos").json()["pagos"][0]


def ruta(pago):
    return f"/api/v1/pagos/{pago['id']}/cambio-de-plan"


def test_la_vista_previa_conserva_el_inicio_y_calcula_la_diferencia(
    administracion, pago_de_ana, trimestral
):
    r = administracion.get(ruta(pago_de_ana), {"planId": trimestral["id"]})
    cuerpo = r.json()
    assert (cuerpo["inicia"], cuerpo["vence"]) == ("2026-09-22", "2026-12-20")
    assert (cuerpo["valor"], cuerpo["diferencia"]) == (200000, 125000)
    assert PagoModelo.objects.filter(id=pago_de_ana["id"], fecha_anulacion__isnull=True).exists()


def test_cambiar_de_mensual_a_trimestral(administracion, pago_de_ana, trimestral):
    r = administracion.post(
        ruta(pago_de_ana),
        {"planId": trimestral["id"], "medio": "EFECTIVO", "motivo": "Pidió el plan Trimestral"},
    )
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["anulado"]["estado"] == "ANULADO"
    assert cuerpo["anulado"]["anulacion"]["motivo"] == "Pidió el plan Trimestral"
    assert (cuerpo["nuevo"]["plan"], cuerpo["nuevo"]["inicia"], cuerpo["nuevo"]["vence"]) == (
        "Trimestral",
        "2026-09-22",
        "2026-12-20",
    )
    assert (cuerpo["nuevo"]["valor"], cuerpo["diferencia"]) == (200000, 125000)
    historial = administracion.get("/api/v1/socios/CC/1090123456/pagos").json()
    assert [p["estado"] for p in historial["pagos"]] == ["VIGENTE", "ANULADO"]
    assert historial["estado"]["venceEl"] == "2026-12-20"


def test_el_comprobante_del_pago_anulado_se_puede_volver_a_usar(administracion, trimestral):
    pago = {"id": str(ID_PAGO_JORGE)}
    r = administracion.post(
        ruta(pago),
        {
            "planId": trimestral["id"],
            "medio": "NEQUI",
            "referencia": "M123456",
            "motivo": "Cambio a Trimestral",
        },
    )
    assert r.status_code == 201
    assert r.json()["nuevo"]["referencia"] == "M123456"


def test_si_el_pago_nuevo_falla_la_anulacion_no_queda(administracion, pago_de_ana, trimestral):
    r = administracion.post(
        ruta(pago_de_ana),
        {
            "planId": trimestral["id"],
            "medio": "NEQUI",
            "referencia": "M123456",
            "motivo": "Cambio con comprobante ajeno",
        },
    )
    assert (r.status_code, r.json()["codigo"]) == (409, "COMPROBANTE_DUPLICADO")
    assert PagoModelo.objects.filter(id=pago_de_ana["id"], fecha_anulacion__isnull=True).exists()


def test_no_se_cambia_al_mismo_plan(administracion, pago_de_ana):
    r = administracion.get(ruta(pago_de_ana), {"planId": str(ID_MENSUAL)})
    assert r.status_code == 400


def test_un_pago_ya_anulado_no_se_cambia(administracion, pago_de_ana, trimestral):
    administracion.patch(
        f"/api/v1/pagos/{pago_de_ana['id']}", {"estado": "ANULADO", "motivo": "Error de digitación"}
    )
    r = administracion.post(
        ruta(pago_de_ana), {"planId": trimestral["id"], "medio": "EFECTIVO", "motivo": "Cambio"}
    )
    assert r.status_code == 409


def test_la_recepcionista_no_cambia_planes(api, pago_de_ana, trimestral):
    recepcion = ClienteAPI(Client()).como("laura@gimnasio-demo.co")
    r = recepcion.post(
        ruta(pago_de_ana), {"planId": trimestral["id"], "medio": "EFECTIVO", "motivo": "Cambio"}
    )
    assert r.status_code == 403
