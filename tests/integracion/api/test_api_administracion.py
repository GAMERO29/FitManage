"""Lo que el aplicativo necesita además de recepción (Guía 16, ADR N.° 17).

Vista previa del pago, historial del socio, precio de los planes y cuentas del personal. Cada
respuesta se valida contra el contrato con `ClienteAPI`.
"""

import uuid

import pytest
from apoyo_api import ID_MENSUAL

from infraestructura import cuentas
from infraestructura.persistencia.models import PagoModelo

PREVIA = "/api/v1/pagos/vista-previa"
PERSONAL = "/api/v1/personal"


@pytest.fixture
def administracion(api):
    return api.como("carlos@gimnasio-demo.co")


@pytest.fixture
def recepcion(api):
    return api.como("laura@gimnasio-demo.co")


# --- Vista previa del pago ---------------------------------------------------------------
def test_la_renovacion_anticipada_empieza_al_dia_siguiente_del_vencimiento(recepcion):
    cuerpo = recepcion.get(
        PREVIA, {"tipoDocumento": "CC", "numeroDocumento": "1090123456", "planId": str(ID_MENSUAL)}
    ).json()
    assert (cuerpo["inicia"], cuerpo["vence"], cuerpo["valor"]) == (
        "2026-10-22",
        "2026-11-20",
        75000,
    )
    assert cuerpo["diasDesdeHoy"] == 45  # 15 que le quedan + 30 del plan


def test_un_socio_vencido_empieza_hoy_y_la_vista_previa_no_guarda_nada(recepcion):
    antes = PagoModelo.objects.count()
    cuerpo = recepcion.get(
        PREVIA, {"tipoDocumento": "CC", "numeroDocumento": "1093445566", "planId": str(ID_MENSUAL)}
    ).json()
    assert (cuerpo["inicia"], cuerpo["vence"], cuerpo["diasDesdeHoy"]) == (
        "2026-10-07",
        "2026-11-05",
        30,
    )
    assert PagoModelo.objects.count() == antes


def test_vista_previa_de_un_documento_que_no_existe(recepcion):
    r = recepcion.get(
        PREVIA, {"tipoDocumento": "CC", "numeroDocumento": "1111111111", "planId": str(ID_MENSUAL)}
    )
    assert r.status_code == 404


def test_vista_previa_sin_plan_es_una_solicitud_invalida(recepcion):
    r = recepcion.get(PREVIA, {"tipoDocumento": "CC", "numeroDocumento": "1090123456"})
    assert r.status_code == 400


# --- Historial del socio -----------------------------------------------------------------
def test_el_historial_trae_pagos_vigentes_y_anulados(administracion):
    ruta = "/api/v1/socios/CC/1090123456/pagos"
    pago = administracion.get(ruta).json()["pagos"][0]
    administracion.patch(
        f"/api/v1/pagos/{pago['id']}", {"estado": "ANULADO", "motivo": "Pago de prueba"}
    )
    cuerpo = administracion.get(ruta).json()
    assert cuerpo["socio"]["nombreCompleto"] == "Ana Pérez"
    assert cuerpo["socio"]["documentoEnmascarado"] == "CC ******3456"
    assert [p["estado"] for p in cuerpo["pagos"]] == ["ANULADO"]
    assert cuerpo["pagos"][0]["anulacion"]["anuladoPor"] == "Carlos"
    assert cuerpo["estado"]["estado"] == "SIN_MEMBRESIA"


def test_la_recepcionista_no_ve_el_historial(recepcion):
    assert recepcion.get("/api/v1/socios/CC/1090123456/pagos").status_code == 403


def test_historial_de_un_socio_que_no_existe(administracion):
    assert administracion.get("/api/v1/socios/CC/1111111111/pagos").status_code == 404


# --- Precio de los planes ----------------------------------------------------------------
def test_el_precio_nuevo_solo_vale_para_los_pagos_siguientes(administracion):
    plan = administracion.patch(f"/api/v1/planes/{ID_MENSUAL}", {"precio": 80000}).json()
    assert plan["precio"] == 80000
    nuevo = administracion.post(
        "/api/v1/pagos",
        {
            "tipoDocumento": "PPT",
            "numeroDocumento": "25789456",
            "planId": str(ID_MENSUAL),
            "medio": "EFECTIVO",
        },
        {"Idempotency-Key": str(uuid.uuid4())},
    ).json()
    assert nuevo["valor"] == 80000
    anterior = administracion.get("/api/v1/socios/CC/1090123456/pagos").json()["pagos"][0]
    assert anterior["valor"] == 75000


@pytest.mark.parametrize("precio", [0, -5, 75000.5], ids=["cero", "negativo", "decimal"])
def test_el_precio_debe_ser_un_entero_positivo(administracion, precio):
    r = administracion.patch(f"/api/v1/planes/{ID_MENSUAL}", {"precio": precio})
    assert r.status_code == 400


def test_la_recepcionista_no_cambia_precios(recepcion):
    r = recepcion.patch(f"/api/v1/planes/{ID_MENSUAL}", {"precio": 1000})
    assert r.status_code == 403


def test_cambiar_el_precio_de_un_plan_que_no_existe(administracion):
    r = administracion.patch(f"/api/v1/planes/{uuid.uuid4()}", {"precio": 1000})
    assert r.status_code == 404


# --- Cuentas del personal ----------------------------------------------------------------
def test_el_token_trae_el_nombre_para_la_interfaz(api):
    r = api.post(
        "/api/v1/auth/token", {"correo": "laura@gimnasio-demo.co", "contrasena": "demo2026"}
    )
    assert (r.json()["nombre"], r.json()["rol"]) == ("Laura", "RECEPCIONISTA")


def test_lista_las_cuentas_sin_contrasenas(administracion):
    cuerpo = administracion.get(PERSONAL).json()
    assert [c["nombre"] for c in cuerpo] == ["Carlos", "Diego Salcedo", "Laura"]
    assert all(not c["bloqueada"] for c in cuerpo)
    assert all("clave" not in str(c).lower() for c in cuerpo)


def test_crear_una_cuenta_y_entrar_con_ella(administracion, client):
    r = administracion.post(
        PERSONAL,
        {
            "nombre": "Sofía Rueda",
            "correo": "Sofia@Gimnasio-Demo.co",
            "rol": "RECEPCIONISTA",
            "contrasena": "clave-inicial-2026",
        },
    )
    assert r.status_code == 201
    assert r.json()["correo"] == "sofia@gimnasio-demo.co"
    entrada = client.post(
        "/api/v1/auth/token",
        {"correo": "sofia@gimnasio-demo.co", "contrasena": "clave-inicial-2026"},
        content_type="application/json",
    )
    assert entrada.status_code == 200


def test_no_se_repite_un_correo_aunque_cambien_las_mayusculas(administracion):
    r = administracion.post(
        PERSONAL,
        {
            "nombre": "Otra Laura",
            "correo": "LAURA@gimnasio-demo.co",
            "rol": "RECEPCIONISTA",
            "contrasena": "clave-inicial-2026",
        },
    )
    assert (r.status_code, r.json()["codigo"]) == (409, "CORREO_DUPLICADO")


def test_dos_altas_simultaneas_del_mismo_correo(administracion, monkeypatch):
    """Si la revisión previa no lo ve (otra alta en paralelo), lo ataja el índice único."""
    monkeypatch.setattr(cuentas, "_correo_en_uso", lambda correo: False)
    r = administracion.post(
        PERSONAL,
        {
            "nombre": "Laura",
            "correo": "laura@gimnasio-demo.co",
            "rol": "RECEPCIONISTA",
            "contrasena": "clave-inicial-2026",
        },
    )
    assert r.status_code == 409


def test_la_contrasena_inicial_tiene_al_menos_12_caracteres(administracion):
    r = administracion.post(
        PERSONAL,
        {
            "nombre": "Sofía",
            "correo": "s@gimnasio-demo.co",
            "rol": "RECEPCIONISTA",
            "contrasena": "corta",
        },
    )
    assert r.status_code == 400


def test_la_recepcionista_no_administra_cuentas(recepcion):
    assert recepcion.get(PERSONAL).status_code == 403


def test_desbloquear_una_cuenta_antes_de_los_15_minutos(administracion, client):
    for _ in range(5):
        client.post(
            "/api/v1/auth/token",
            {"correo": "laura@gimnasio-demo.co", "contrasena": "equivocada"},
            content_type="application/json",
        )
    laura = next(c for c in administracion.get(PERSONAL).json() if c["nombre"] == "Laura")
    assert laura["bloqueada"] and "bloqueadaHasta" in laura
    desbloqueada = administracion.post(f"{PERSONAL}/{laura['id']}/desbloqueo").json()
    assert desbloqueada["bloqueada"] is False
    entrada = client.post(
        "/api/v1/auth/token",
        {"correo": "laura@gimnasio-demo.co", "contrasena": "demo2026"},
        content_type="application/json",
    )
    assert entrada.status_code == 200


def test_desbloquear_una_cuenta_que_no_existe(administracion):
    assert administracion.post(f"{PERSONAL}/{uuid.uuid4()}/desbloqueo").status_code == 404
