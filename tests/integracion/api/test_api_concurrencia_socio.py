"""Guía II-01, D-01 y D-02: dos operaciones de pago sobre el mismo socio no se intercalan.

Solo PostgreSQL: SQLite no tiene `SELECT ... FOR UPDATE` y serializa toda la base.
Cada hilo lee los pagos vigentes y espera 0,4 s antes de escribir, para que el cruce ocurra
siempre y no dependa de la suerte. Sin el bloqueo del socio, las dos pruebas fallan.
"""

from __future__ import annotations

import json
import threading
import time
import uuid

import pytest
from apoyo_api import CLAVE, ID_PAGO_JORGE, sembrar
from django.db import connection, connections
from django.test import Client

from infraestructura.persistencia.models import EventoAuditoriaModelo, PagoModelo
from infraestructura.persistencia.repositorios import PagoRepositorioORM

pytestmark = pytest.mark.skipif(
    connection.vendor != "postgresql", reason="el bloqueo de fila se prueba en PostgreSQL"
)

_vigentes_original = PagoRepositorioORM.vigentes_de


def _vigentes_lento(self, socio):
    resultado = _vigentes_original(self, socio)
    time.sleep(0.4)
    return resultado


@pytest.fixture
def datos(transactional_db, reloj, monkeypatch):
    monkeypatch.setattr(PagoRepositorioORM, "vigentes_de", _vigentes_lento)
    return sembrar()


def _token(correo: str) -> str:
    respuesta = Client().post(
        "/api/v1/auth/token",
        json.dumps({"correo": correo, "contrasena": CLAVE}),
        "application/json",
    )
    return respuesta.json()["tokenAcceso"]


def _a_la_vez(*peticiones):
    """Lanza las peticiones en hilos que arrancan juntos y devuelve sus códigos HTTP."""
    barrera = threading.Barrier(len(peticiones))
    codigos: list[int | None] = [None] * len(peticiones)

    def correr(i, peticion):
        try:
            barrera.wait(timeout=10)
            codigos[i] = peticion().status_code
        finally:
            connections.close_all()

    hilos = [threading.Thread(target=correr, args=par) for par in enumerate(peticiones)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=30)
    return codigos


def test_d01_dos_anulaciones_del_mismo_pago_solo_una_tiene_exito(datos):
    token = _token("carlos@gimnasio-demo.co")

    def anular(motivo):
        return lambda: Client().patch(
            f"/api/v1/pagos/{ID_PAGO_JORGE}",
            json.dumps({"estado": "ANULADO", "motivo": motivo}),
            "application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

    codigos = _a_la_vez(anular("Plan equivocado"), anular("Valor equivocado"))

    assert sorted(codigos) == [200, 409]  # RN-07: la anulación ocurre una sola vez
    fila = PagoModelo.objects.get(id=ID_PAGO_JORGE)
    assert fila.estado == "ANULADO"
    # Guía II-03: el rastro también queda una sola vez, con el motivo que sí se guardó.
    (evento,) = EventoAuditoriaModelo.objects.filter(tipo="PAGO_ANULADO")
    assert evento.detalle["motivo"] == fila.motivo_anulacion


def test_d02_dos_pagos_del_mismo_socio_al_tiempo_no_se_superponen(datos):
    tokens = [_token("laura@gimnasio-demo.co"), _token("carlos@gimnasio-demo.co")]
    mensual = str(datos["mensual"].id)

    def pagar(token, referencia):
        return lambda: Client().post(
            "/api/v1/pagos",
            json.dumps(
                {
                    "tipoDocumento": "CC",
                    "numeroDocumento": "1090123456",  # Ana, activa hasta el 21/10/2026
                    "planId": mensual,
                    "medio": "NEQUI",
                    "referencia": referencia,
                }
            ),
            "application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )

    codigos = _a_la_vez(pagar(tokens[0], "M200001"), pagar(tokens[1], "M200002"))

    assert codigos == [201, 201]
    inicios = sorted(
        str(f)
        for f in PagoModelo.objects.filter(
            socio_id=datos["ana"].id, referencia__in=["M200001", "M200002"]
        ).values_list("fecha_inicio", flat=True)
    )
    # RN-04: el segundo pago empieza el día siguiente al vencimiento del primero.
    assert inicios == ["2026-10-22", "2026-11-21"]
    assert EventoAuditoriaModelo.objects.filter(tipo="PAGO_REGISTRADO").count() == 2


def test_anular_y_pagar_al_tiempo_deja_un_resultado_que_existe_en_algun_orden(datos):
    """El resultado debe ser el de hacer una operación después de la otra, en cualquier orden."""
    laura, carlos = _token("laura@gimnasio-demo.co"), _token("carlos@gimnasio-demo.co")
    ana = datos["ana"]
    ultimo = PagoModelo.objects.get(socio_id=ana.id, estado="VIGENTE")

    def anular():
        return Client().patch(
            f"/api/v1/pagos/{ultimo.id}",
            json.dumps({"estado": "ANULADO", "motivo": "Plan equivocado"}),
            "application/json",
            HTTP_AUTHORIZATION=f"Bearer {carlos}",
        )

    def pagar():
        return Client().post(
            "/api/v1/pagos",
            json.dumps(
                {
                    "tipoDocumento": "CC",
                    "numeroDocumento": "1090123456",
                    "planId": str(datos["mensual"].id),
                    "medio": "EFECTIVO",
                }
            ),
            "application/json",
            HTTP_AUTHORIZATION=f"Bearer {laura}",
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )

    codigo_anular, codigo_pagar = _a_la_vez(anular, pagar)

    nuevo = PagoModelo.objects.exclude(id=ultimo.id).get(socio_id=ana.id)
    assert codigo_pagar == 201
    if codigo_anular == 200:  # primero se anuló: el pago nuevo empieza hoy, 7/10
        assert str(nuevo.fecha_inicio) == "2026-10-07"
    else:  # primero se pagó: el anterior ya no es el último y no se anula
        assert codigo_anular == 409
        assert str(nuevo.fecha_inicio) == "2026-10-22"
