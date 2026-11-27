"""Software III, Guía 06: DELETE /socios/{tipo}/{numero} por las capas, con los tres caminos.

El éxito, el rechazo por regla (el socio tiene pagos) y la falla de la base, que sale como 503
en problem+json y no como el 500 en HTML que encontró la Guía 02.
"""

import pytest
from django.db import OperationalError

from infraestructura.api import vistas
from infraestructura.persistencia.models import EventoAuditoriaModelo, SocioModelo

MARIA = "/api/v1/socios/PPT/25789456"  # sin pagos en los datos de demostración
ANA = "/api/v1/socios/CC/1090123456"  # con un pago


@pytest.fixture
def administracion(api):
    return api.como("carlos@gimnasio-demo.co")


def test_suprime_los_datos_de_una_socia_sin_pagos(administracion):
    r = administracion.delete(MARIA)
    assert r.status_code == 204
    assert r.content == b""  # auditoría de IA de la Guía 06: no se devuelve el socio suprimido
    assert not SocioModelo.objects.filter(numero_documento="25789456").exists()
    assert administracion.get("/api/v1/estados/PPT/25789456").status_code == 404
    evento = EventoAuditoriaModelo.objects.get(tipo="SOCIO_SUPRIMIDO")
    assert evento.detalle == {} and evento.socio_id is None and evento.actor_nombre == "Carlos"


def test_repetir_la_supresion_responde_404(administracion):
    assert administracion.delete(MARIA).status_code == 204
    r = administracion.delete(MARIA)
    assert r.status_code == 404 and r.json()["codigo"] == "NO_ENCONTRADO"
    assert EventoAuditoriaModelo.objects.filter(tipo="SOCIO_SUPRIMIDO").count() == 1


def test_un_socio_con_pagos_no_se_suprime(administracion):
    r = administracion.delete(ANA)
    assert r.status_code == 409 and r.json()["codigo"] == "SOCIO_CON_PAGOS"
    assert SocioModelo.objects.filter(numero_documento="1090123456").exists()
    assert not EventoAuditoriaModelo.objects.filter(tipo="SOCIO_SUPRIMIDO").exists()


def test_la_recepcionista_no_suprime(api):
    r = api.como("laura@gimnasio-demo.co").delete(MARIA)
    assert r.status_code == 403
    assert SocioModelo.objects.filter(numero_documento="25789456").exists()


def _base_caida(*_args, **_kwargs):
    raise OperationalError("connection refused")


def test_si_la_base_no_responde_es_503_y_no_cambia_nada(administracion, monkeypatch):
    monkeypatch.setattr(vistas, "bloquear_socio_por_documento", _base_caida)
    r = administracion.delete(MARIA)
    assert r.status_code == 503 and r["Content-Type"] == "application/problem+json"
    assert r.json()["codigo"] == "SERVICIO_NO_DISPONIBLE" and r["Retry-After"] == "60"
    monkeypatch.undo()
    assert SocioModelo.objects.filter(numero_documento="25789456").exists()


def test_la_consulta_de_estado_con_la_base_caida_es_503_en_problem_json(api, monkeypatch):
    """El hallazgo de la Guía 02: antes salía la página HTML del 500 de Django."""
    recepcion = api.como("laura@gimnasio-demo.co")

    class ConsultaCaida:
        def consultar(self, *_):
            raise OperationalError("connection refused")

    monkeypatch.setattr(vistas.contenedor, "consulta_estado", ConsultaCaida)
    r = recepcion.get("/api/v1/estados/CC/1090123456")
    assert r.status_code == 503 and r.json()["codigo"] == "SERVICIO_NO_DISPONIBLE"
