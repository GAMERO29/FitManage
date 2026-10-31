"""Reportes, vencimientos y planes: modelos de lectura (RF-05, RF-06)."""

import uuid

import pytest

PAGOS = "/api/v1/pagos"


@pytest.fixture
def administracion(api):
    return api.como("carlos@gimnasio-demo.co")


def test_planes_activos_con_precio(api):
    cuerpo = api.como("laura@gimnasio-demo.co").get("/api/v1/planes").json()
    assert [(p["nombre"], p["duracionDias"], p["precio"]) for p in cuerpo] == [
        ("Diario", 1, 8000),
        ("Mensual", 30, 75000),
        ("Trimestral", 90, 200000),
    ]


def test_reporte_suma_por_medio_y_excluye_anulados(administracion, gimnasio):
    for medio, ref in (("NEQUI", "M700001"), ("EFECTIVO", None)):
        cuerpo = {
            "tipoDocumento": "PPT",
            "numeroDocumento": "25789456",
            "planId": str(gimnasio["diario"].id),
            "medio": medio,
        } | ({"referencia": ref} if ref else {})
        ultimo = administracion.post(PAGOS, cuerpo, {"Idempotency-Key": str(uuid.uuid4())}).json()
    administracion.patch(
        f"{PAGOS}/{ultimo['id']}", {"estado": "ANULADO", "motivo": "Pago de prueba"}
    )
    r = administracion.get(
        "/api/v1/reportes/ingresos", {"desde": "2026-10-01", "hasta": "2026-10-07"}
    )
    cuerpo = r.json()
    assert (cuerpo["total"], cuerpo["pagos"], cuerpo["anulados"]) == (8000, 1, 1)
    nequi = next(m for m in cuerpo["porMedio"] if m["medio"] == "NEQUI")
    assert (nequi["pagos"], nequi["total"]) == (1, 8000)
    assert sum(m["total"] for m in cuerpo["porMedio"]) == cuerpo["total"]


def test_el_reporte_no_incluye_pagos_fuera_del_rango(administracion):
    cuerpo = administracion.get(
        "/api/v1/reportes/ingresos", {"desde": "2026-09-01", "hasta": "2026-09-30"}
    ).json()
    assert (cuerpo["total"], cuerpo["pagos"]) == (75000, 1)  # solo el de Ana del 22/09


@pytest.mark.parametrize(
    "rango",
    [
        {"desde": "2026-10-07", "hasta": "2026-10-01"},
        {"desde": "2025-01-01", "hasta": "2026-10-07"},
    ],
    ids=["invertido", "mas-de-un-ano"],
)
def test_rango_invalido_es_400(administracion, rango):
    assert administracion.get("/api/v1/reportes/ingresos", rango).status_code == 400


def test_la_recepcionista_no_ve_ingresos(api):
    """PA-07 / QA-04."""
    r = api.como("laura@gimnasio-demo.co").get(
        "/api/v1/reportes/ingresos", {"desde": "2026-10-01", "hasta": "2026-10-07"}
    )
    assert r.status_code == 403 and "total" not in r.json()


def test_vencimientos_con_enlace_de_whatsapp(api):
    recepcion = api.como("laura@gimnasio-demo.co")
    assert recepcion.get("/api/v1/vencimientos").json() == []
    [ana] = recepcion.get("/api/v1/vencimientos", {"dias": 15}).json()
    assert (ana["nombreCorto"], ana["plan"], ana["venceEl"]) == ("Ana P.", "Mensual", "2026-10-21")
    assert ana["enlaceWhatsApp"].startswith("https://wa.me/573000000005?text=Hola%20Ana")


def test_dias_fuera_de_rango_es_400(api):
    assert (
        api.como("laura@gimnasio-demo.co").get("/api/v1/vencimientos", {"dias": 99}).status_code
        == 400
    )
