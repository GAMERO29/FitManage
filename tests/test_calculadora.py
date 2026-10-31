from datetime import date

import pytest
from fechas import bogota

from dominio.calculadora import CalculadoraMembresia
from dominio.modelos import EstadoMembresia

calc = CalculadoraMembresia()


@pytest.mark.parametrize(
    ("inicio", "dias", "vence"),
    [
        (date(2026, 3, 1), 90, date(2026, 5, 29)),  # CP-03a trimestral
        (date(2026, 10, 7), 1, date(2026, 10, 7)),  # plan diario vence hoy
        (date(2026, 10, 7), 15, date(2026, 10, 21)),  # quincenal
        (date(2026, 10, 7), 30, date(2026, 11, 5)),  # mensual
    ],
)
def test_vencimiento_es_inicio_mas_duracion_menos_uno(inicio, dias, vence):
    assert calc.calcular_vencimiento(inicio, dias) == vence


def test_sin_pagos_el_periodo_inicia_hoy():
    assert calc.calcular_fecha_inicio([], date(2026, 10, 7)) == date(2026, 10, 7)


def test_socio_vencido_inicia_hoy(ana, mensual, laura, fabrica_pago):
    pago = fabrica_pago(ana, mensual, date(2026, 8, 31), date(2026, 9, 29), laura)
    assert calc.calcular_fecha_inicio([pago], date(2026, 10, 7)) == date(2026, 10, 7)


def test_renovacion_anticipada_inicia_al_dia_siguiente_del_vencimiento(
    ana, mensual, laura, fabrica_pago
):
    # CP-03b: vence 15/04, paga el 10/04 → inicia 16/04
    pago = fabrica_pago(ana, mensual, date(2026, 3, 17), date(2026, 4, 15), laura)
    assert calc.calcular_fecha_inicio([pago], date(2026, 4, 10)) == date(2026, 4, 16)


def test_renovar_el_mismo_dia_del_vencimiento_inicia_manana(ana, mensual, laura, fabrica_pago):
    pago = fabrica_pago(ana, mensual, date(2026, 9, 8), date(2026, 10, 7), laura)
    assert calc.calcular_fecha_inicio([pago], date(2026, 10, 7)) == date(2026, 10, 8)


def test_pagos_anulados_no_cuentan_para_el_inicio(ana, mensual, laura, carlos, fabrica_pago):
    pago = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    pago.anular("Error", carlos, bogota(2026, 10, 7, 19, 0))
    assert calc.calcular_fecha_inicio([pago], date(2026, 10, 7)) == date(2026, 10, 7)


def test_estado_activo_con_vencimiento_futuro(ana, mensual, laura, fabrica_pago):
    pago = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    assert calc.estado_de([pago], date(2026, 10, 20)) == (
        EstadoMembresia.ACTIVO,
        date(2026, 11, 5),
    )


def test_socio_que_vence_hoy_sigue_activo(ana, mensual, laura, fabrica_pago):
    # CP-04e
    pago = fabrica_pago(ana, mensual, date(2026, 9, 8), date(2026, 10, 7), laura)
    assert calc.estado_de([pago], date(2026, 10, 7))[0] is EstadoMembresia.ACTIVO


def test_estado_vencido_y_dias_de_mora(ana, mensual, laura, fabrica_pago):
    pago = fabrica_pago(ana, mensual, date(2026, 8, 31), date(2026, 9, 29), laura)
    assert calc.estado_de([pago], date(2026, 10, 7))[0] is EstadoMembresia.VENCIDO
    assert calc.dias_de_mora([pago], date(2026, 10, 7)) == 8


def test_socio_sin_pagos_queda_sin_membresia():
    assert calc.estado_de([], date(2026, 10, 7)) == (
        EstadoMembresia.SIN_MEMBRESIA,
        None,
    )


def test_socio_con_solo_pagos_anulados_queda_sin_membresia(
    ana, mensual, laura, carlos, fabrica_pago
):
    pago = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    pago.anular("Error", carlos, bogota(2026, 10, 7, 19, 0))
    assert calc.estado_de([pago], date(2026, 10, 7))[0] is EstadoMembresia.SIN_MEMBRESIA


def test_con_varios_pagos_manda_el_vencimiento_mas_lejano(ana, mensual, laura, fabrica_pago):
    viejo = fabrica_pago(ana, mensual, date(2026, 9, 8), date(2026, 10, 7), laura)
    nuevo = fabrica_pago(ana, mensual, date(2026, 10, 8), date(2026, 11, 6), laura)
    assert calc.estado_de([nuevo, viejo], date(2026, 10, 7))[1] == date(2026, 11, 6)
