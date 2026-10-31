"""Recepción: el esquema público del estado (OHS de Membresías, QA-01 y Ley 1581 de 2012)."""

import pytest
from apoyo_api import AHORA
from dobles import RelojFijo
from fechas import bogota

from dominio.modelos import TipoDocumento
from infraestructura.api import contenedor, presentacion


@pytest.fixture
def recepcion(api):
    return api.como("laura@gimnasio-demo.co")


def test_socia_activa_con_los_dias_que_le_quedan(recepcion):
    r = recepcion.get("/api/v1/estados/CC/1090123456")
    assert r.status_code == 200
    assert r.json() == {
        "documentoHash": presentacion.huella_documento(TipoDocumento.CC, "1090123456"),
        "nombreCorto": "Ana P.",
        "documentoEnmascarado": "CC ******3456",
        "estado": "ACTIVO",
        "venceEl": "2026-10-21",
        "diasRestantes": 15,
    }


def test_socio_vencido_con_dias_de_mora(recepcion):
    cuerpo = recepcion.get("/api/v1/estados/CC/1093445566").json()
    assert (cuerpo["estado"], cuerpo["diasMora"], cuerpo["venceEl"]) == ("VENCIDO", 8, "2026-09-29")
    assert "diasRestantes" not in cuerpo


def test_socia_registrada_sin_membresia(recepcion):
    cuerpo = recepcion.get("/api/v1/estados/PPT/25789456").json()
    assert cuerpo["estado"] == "SIN_MEMBRESIA" and "venceEl" not in cuerpo
    assert cuerpo["nombreCorto"] == "María G."


def test_la_respuesta_no_trae_telefono_ni_documento_completo(recepcion):
    texto = recepcion.get("/api/v1/estados/CC/1090123456").content.decode()
    assert "3000000005" not in texto and "1090123456" not in texto


def test_documento_inexistente_es_404(recepcion):
    r = recepcion.get("/api/v1/estados/CC/1111111111")
    assert r.status_code == 404 and r.json()["codigo"] == "NO_ENCONTRADO"


def test_tipo_de_documento_fuera_del_contrato_es_400(recepcion):
    assert recepcion.get("/api/v1/estados/TI/1090123456").status_code == 400


def test_a_las_7_30_pm_un_socio_que_vence_hoy_sigue_activo(recepcion, monkeypatch):
    """PA-05 / QA-03: con un servidor en UTC, a las 7:30 p. m. ya sería otro día."""
    monkeypatch.setattr(contenedor, "reloj", lambda: RelojFijo(bogota(2026, 10, 21, 19, 30)))
    cuerpo = recepcion.get("/api/v1/estados/CC/1090123456").json()
    assert (cuerpo["estado"], cuerpo["diasRestantes"]) == ("ACTIVO", 1)


def test_el_entrenador_no_consulta_estados(api):
    assert (
        api.como("diego@gimnasio-demo.co").get("/api/v1/estados/CC/1090123456").status_code == 403
    )


def test_lista_para_la_cache_sin_conexion(recepcion):
    cuerpo = recepcion.get("/api/v1/estados").json()
    assert cuerpo["generadoEl"] == AHORA.isoformat(timespec="seconds")
    assert [e["nombreCorto"] for e in cuerpo["estados"]] == ["María G.", "Ana P.", "Jorge R."]
    assert "telefono" not in str(cuerpo)


def test_lista_solo_con_los_cambios_desde_una_hora(recepcion):
    r = recepcion.get("/api/v1/estados", {"cambiadosDesde": "2026-09-01T00:00:00-05:00"})
    assert [e["nombreCorto"] for e in r.json()["estados"]] == ["Ana P."]
