"""Guía II-03, ítems I-2 (parte de planes, #57) e I-3 (#58): consultar el rastro y sus eventos."""

from __future__ import annotations

import uuid

import pytest
from apoyo_api import ID_MENSUAL, ID_PAGO_JORGE, ClienteAPI
from django.test import Client

from infraestructura import consultas
from infraestructura.persistencia.models import EventoAuditoriaModelo

RUTA = "/api/v1/auditoria"
HOY = {"desde": "2026-10-07", "hasta": "2026-10-07"}  # el reloj de las pruebas: 7/10/2026


@pytest.fixture
def administracion(api):
    return api.como("carlos@gimnasio-demo.co")


@pytest.fixture
def recepcion(api):
    return ClienteAPI(Client()).como("laura@gimnasio-demo.co")


def test_el_administrador_ve_el_evento_con_el_socio_enmascarado(administracion):
    administracion.patch(
        f"/api/v1/pagos/{ID_PAGO_JORGE}", {"estado": "ANULADO", "motivo": "Valor equivocado"}
    )
    r = administracion.get(RUTA, HOY)
    assert r.status_code == 200
    (evento,) = r.json()["eventos"]
    assert evento["tipo"] == "PAGO_ANULADO" and evento["actor"] == "Carlos"
    assert evento["socio"] == {"nombre": "Jorge Rincón", "documentoEnmascarado": "CC ******5566"}
    assert evento["ocurridoEl"].endswith("-05:00")


@pytest.mark.parametrize("correo", ["laura@gimnasio-demo.co", "diego@gimnasio-demo.co"])
def test_solo_el_administrador_consulta_la_auditoria(api, correo):
    r = ClienteAPI(Client()).como(correo).get(RUTA, HOY)
    assert r.status_code == 403


@pytest.mark.parametrize(
    "rango",
    [
        {"desde": "2026-10-07", "hasta": "2026-10-06"},
        {"desde": "2026-09-01", "hasta": "2026-10-03"},
    ],
    ids=["hasta-antes-de-desde", "mas-de-31-dias"],
)
def test_rango_invalido_es_400(administracion, rango):
    assert administracion.get(RUTA, rango).status_code == 400


def test_31_dias_exactos_se_aceptan(administracion):
    r = administracion.get(RUTA, {"desde": "2026-09-06", "hasta": "2026-10-07"})
    assert r.status_code == 200


def test_paginas_del_mas_reciente_al_mas_antiguo(administracion, recepcion, monkeypatch):
    monkeypatch.setattr(consultas, "POR_PAGINA_AUDITORIA", 2)
    for referencia in ("M900001", "M900002", "M900003"):
        recepcion.post(
            "/api/v1/pagos",
            {
                "tipoDocumento": "CC",
                "numeroDocumento": "1090123456",
                "planId": str(ID_MENSUAL),
                "medio": "NEQUI",
                "referencia": referencia,
            },
            {"Idempotency-Key": str(uuid.uuid4())},
        )
    primera = administracion.get(RUTA, HOY).json()
    segunda = administracion.get(RUTA, {**HOY, "pagina": 2}).json()
    assert primera["total"] == segunda["total"] == 3
    referencias = [e["detalle"]["referencia"] for e in primera["eventos"] + segunda["eventos"]]
    assert referencias == ["M900003", "M900002", "M900001"]


def test_cambiar_precio_y_desactivar_dejan_eventos(administracion, gimnasio):
    diario = gimnasio["diario"]
    administracion.patch(f"/api/v1/planes/{diario.id}", {"precio": 9000})
    administracion.patch(f"/api/v1/planes/{diario.id}", {"activo": False})
    administracion.patch(f"/api/v1/planes/{diario.id}", {"precio": 9000})  # mismo precio: nada
    tipos = list(EventoAuditoriaModelo.objects.order_by("id").values_list("tipo", "detalle"))
    assert tipos == [
        ("PRECIO_CAMBIADO", {"plan": "Diario", "antes": 8000, "despues": 9000}),
        ("PLAN_DESACTIVADO", {"plan": "Diario"}),
    ]


def test_crear_un_plan_deja_evento(administracion):
    r = administracion.post(
        "/api/v1/planes", {"nombre": "Semestral", "duracionDias": 180, "precio": 380000}
    )
    assert r.status_code == 201
    (evento,) = EventoAuditoriaModelo.objects.all()
    assert evento.tipo == "PLAN_CREADO" and evento.detalle["precio"] == 380000


def test_la_pagina_trae_50_y_la_siguiente_el_resto(administracion, gimnasio):
    """Guía II-04, mutación M8: ninguna prueba fijaba el tamaño de página del contrato."""
    from apoyo_api import AHORA

    EventoAuditoriaModelo.objects.bulk_create(
        EventoAuditoriaModelo(
            ocurrido_en=AHORA,
            tipo="PRECIO_CAMBIADO",
            actor_nombre="Carlos",
            entidad_id=gimnasio["diario"].id,
            detalle={"plan": "Diario", "antes": 8000 + i, "despues": 8001 + i},
        )
        for i in range(51)
    )
    primera = administracion.get(RUTA, HOY).json()
    segunda = administracion.get(RUTA, {**HOY, "pagina": 2}).json()
    assert (primera["porPagina"], primera["total"]) == (50, 51)
    assert (len(primera["eventos"]), len(segunda["eventos"])) == (50, 1)
