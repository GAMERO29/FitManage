"""Guía II-03, ítem I-1 (#56): pagos, anulaciones y cambios de plan dejan un rastro exacto.

El oráculo sale del contrato de la II-02: un evento por operación exitosa, ninguno por un rechazo
o una operación revertida, y nunca el documento ni el teléfono del socio.
"""

from __future__ import annotations

import json
import uuid

import pytest
from apoyo_api import ID_MENSUAL, ID_PAGO_JORGE, ClienteAPI
from django.test import Client

from infraestructura.api import presentacion
from infraestructura.persistencia.models import EventoAuditoriaModelo, PagoModelo

PAGO_NUEVO = {
    "tipoDocumento": "CC",
    "numeroDocumento": "1090123456",
    "planId": str(ID_MENSUAL),
    "medio": "NEQUI",
    "referencia": "M777001",
}


@pytest.fixture
def administracion(api):
    return api.como("carlos@gimnasio-demo.co")


@pytest.fixture
def recepcion(api):
    return ClienteAPI(Client()).como("laura@gimnasio-demo.co")


def eventos(tipo=None):
    consulta = EventoAuditoriaModelo.objects.order_by("id")
    return list(consulta.filter(tipo=tipo) if tipo else consulta)


def pagar(cliente, cuerpo=None):
    return cliente.post(
        "/api/v1/pagos", cuerpo or PAGO_NUEVO, {"Idempotency-Key": str(uuid.uuid4())}
    )


def test_registrar_un_pago_deja_un_evento_con_quien_y_cuanto(recepcion, gimnasio):
    r = pagar(recepcion)
    assert r.status_code == 201
    (evento,) = eventos()
    assert evento.tipo == "PAGO_REGISTRADO"
    assert evento.actor_nombre == "Laura" and evento.actor_id == gimnasio["laura"].id
    assert str(evento.entidad_id) == r.json()["id"]
    assert evento.socio_id == gimnasio["ana"].id
    assert evento.detalle["valor"] == 75000 and evento.detalle["plan"] == "Mensual"
    assert evento.detalle["referencia"] == "M777001"


def test_el_evento_no_guarda_el_documento_ni_el_telefono(recepcion):
    pagar(recepcion)
    texto = json.dumps([e.detalle for e in eventos()])
    assert "1090123456" not in texto and "3000000005" not in texto


def test_anular_deja_el_motivo_y_quien_registro_el_pago(administracion):
    r = administracion.patch(
        f"/api/v1/pagos/{ID_PAGO_JORGE}", {"estado": "ANULADO", "motivo": "Valor equivocado"}
    )
    assert r.status_code == 200
    (evento,) = eventos()
    assert evento.tipo == "PAGO_ANULADO" and evento.actor_nombre == "Carlos"
    assert evento.detalle["motivo"] == "Valor equivocado"
    assert evento.detalle["registradoPor"] == "Laura"  # R13: quién cobró y quién anuló


def test_un_cambio_de_plan_deja_un_solo_evento_con_la_diferencia(administracion, gimnasio):
    pago_ana = administracion.get("/api/v1/socios/CC/1090123456/pagos").json()["pagos"][0]
    r = administracion.post(
        f"/api/v1/pagos/{pago_ana['id']}/cambio-de-plan",
        {"planId": str(gimnasio["diario"].id), "medio": "EFECTIVO", "motivo": "Pidió el diario"},
    )
    assert r.status_code == 201
    (evento,) = eventos()  # ni PAGO_ANULADO ni PAGO_REGISTRADO aparte
    assert evento.tipo == "PLAN_CAMBIADO"
    assert evento.detalle["diferencia"] == r.json()["diferencia"] == 8000 - 75000
    assert evento.detalle["pagoAnulado"] == pago_ana["id"]
    assert evento.detalle["planNuevo"] == "Diario"


@pytest.mark.parametrize(
    "intento",
    ["recepcionista-pago-ajeno", "pago-ya-anulado", "comprobante-repetido"],
)
def test_un_rechazo_no_deja_evento(administracion, recepcion, intento):
    if intento == "recepcionista-pago-ajeno":  # Laura registró a Jorge hace un mes: 403
        r = recepcion.patch(
            f"/api/v1/pagos/{ID_PAGO_JORGE}", {"estado": "ANULADO", "motivo": "Intento ajeno"}
        )
        esperado = 403
    elif intento == "pago-ya-anulado":
        ruta = f"/api/v1/pagos/{ID_PAGO_JORGE}"
        administracion.patch(ruta, {"estado": "ANULADO", "motivo": "Primera vez"})
        r = administracion.patch(ruta, {"estado": "ANULADO", "motivo": "Segunda vez"})
        esperado = 409
    else:  # el segundo pago repite el comprobante del primero
        r = pagar(recepcion)
        r = pagar(recepcion)
        esperado = 409
    assert r.status_code == esperado
    assert len(eventos()) == (0 if intento == "recepcionista-pago-ajeno" else 1)


def test_si_la_operacion_se_revierte_el_evento_tampoco_queda(recepcion, monkeypatch):
    def falla(*_):
        raise RuntimeError("fallo después de guardar, antes de responder")

    monkeypatch.setattr(presentacion, "pago", falla)
    antes = PagoModelo.objects.count()
    with pytest.raises(RuntimeError):
        pagar(recepcion)
    assert PagoModelo.objects.count() == antes
    assert eventos() == []
