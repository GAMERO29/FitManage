"""Escenario QA-03 (fiabilidad temporal) y pago de DT-07."""

from datetime import UTC, date, datetime

import pytest
from fechas import bogota

from dominio.calculadora import CalculadoraMembresia
from dominio.errores import DatosInvalidos
from dominio.modelos import EstadoMembresia, Socio, TipoDocumento
from infraestructura.reloj import RelojBogota

# 7:30 p. m. del 07/10/2026 en Cúcuta = 00:30 del 08/10/2026 en UTC
NOCHE_EN_UTC = datetime(2026, 10, 8, 0, 30, tzinfo=UTC)


def test_reloj_bogota_convierte_la_hora_del_servidor_en_utc():
    reloj = RelojBogota(lambda: NOCHE_EN_UTC)
    assert reloj.hoy() == date(2026, 10, 7)
    assert reloj.ahora().utcoffset().total_seconds() == -5 * 3600


def test_socio_que_vence_hoy_sigue_activo_a_las_7_30_pm(ana, mensual, laura, fabrica_pago):
    # CP-04c: con un servidor en UTC ya sería 08/10 y saldría «Vencido».
    pago = fabrica_pago(ana, mensual, date(2026, 9, 8), date(2026, 10, 7), laura)
    hoy = RelojBogota(lambda: NOCHE_EN_UTC).hoy()
    assert CalculadoraMembresia().estado_de([pago], hoy)[0] is EstadoMembresia.ACTIVO


def test_pago_con_fecha_sin_zona_horaria_se_rechaza(ana, mensual, laura, fabrica_pago):
    with pytest.raises(DatosInvalidos):
        fabrica_pago(
            ana,
            mensual,
            date(2026, 10, 7),
            date(2026, 11, 5),
            laura,
            registrado_en=datetime(2026, 10, 7, 18, 0),  # noqa: DTZ001 (es el caso a rechazar)
        )


def test_anulacion_con_fecha_sin_zona_horaria_se_rechaza(ana, mensual, laura, carlos, fabrica_pago):
    pago = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    with pytest.raises(DatosInvalidos):
        pago.anular("Error", carlos, datetime(2026, 10, 7, 19, 0))  # noqa: DTZ001


def test_autorizacion_de_datos_sin_zona_horaria_se_rechaza():
    sin_zona = datetime(2026, 6, 8, 9, 14)  # noqa: DTZ001 (es el caso a rechazar)
    with pytest.raises(DatosInvalidos):
        Socio(TipoDocumento.CC, "1090000001", "Pedro", "Ríos", "3000000009", sin_zona)


def test_fixture_de_fechas_usa_bogota():
    assert bogota(2026, 10, 7, 19, 30).utcoffset().total_seconds() == -5 * 3600


def test_reloj_real_entrega_la_hora_en_bogota():
    assert RelojBogota().ahora().utcoffset().total_seconds() == -5 * 3600
