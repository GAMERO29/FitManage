"""Software III, Guía 08: el objeto de valor Periodo y las transiciones de la entidad Pago.

Tabla de transición del pago (RN-07):
    VIGENTE  --anular(motivo)--> ANULADO   (misma identidad, queda quién, cuándo y por qué)
    ANULADO  --anular(...)-----> rechazo   (PagoNoAnulable; el estado no cambia)
Frontera de la membresía (RN-03 y RN-05): el día del vencimiento todavía es ACTIVO; el siguiente,
VENCIDO. La recepcionista corrige lo suyo hasta las 23:59:59 de Bogotá (ADR N.° 18).
"""

from dataclasses import replace
from datetime import date

import pytest
from fechas import bogota

from dominio.calculadora import CalculadoraMembresia
from dominio.errores import DatosInvalidos, PagoNoAnulable, PermisoDenegado
from dominio.modelos import EstadoMembresia, EstadoPago, Periodo
from dominio.politicas import RecepcionistaCorrigeSuDia

INICIO = date(2026, 10, 7)
VENCE = date(2026, 11, 5)  # 7 de octubre + 30 días − 1


# Objeto de valor
def test_dos_periodos_con_las_mismas_fechas_son_el_mismo_valor():
    assert Periodo.de_plan(INICIO, 30) == Periodo(INICIO, VENCE)
    assert Periodo(INICIO, VENCE).dias == 30


def test_un_periodo_no_se_modifica_despues_de_creado():
    periodo = Periodo(INICIO, VENCE)
    with pytest.raises(AttributeError):
        periodo.vence = date(2026, 12, 31)


@pytest.mark.parametrize(
    ("inicia", "vence"), [(date(2026, 11, 5), date(2026, 11, 4)), (date(2026, 1, 1), None)]
)
def test_un_periodo_al_reves_o_sin_fin_no_existe(inicia, vence):
    with pytest.raises((DatosInvalidos, TypeError)):
        Periodo(inicia, vence)


@pytest.mark.parametrize("duracion", [0, -30])
def test_un_plan_sin_dias_no_produce_periodo(duracion):
    with pytest.raises(DatosInvalidos):
        Periodo.de_plan(INICIO, duracion)


# Invariante de la entidad: las fechas corresponden a la duración pagada
def test_un_pago_de_30_dias_no_puede_cubrir_90(ana, mensual, laura, fabrica_pago):
    with pytest.raises(DatosInvalidos, match="duración del plan"):
        fabrica_pago(ana, mensual, INICIO, date(2027, 1, 4), laura)


def test_rehidratar_un_pago_tambien_revisa_la_invariante(ana, mensual, laura, fabrica_pago):
    """Copiar con otras fechas pasa por __post_init__: no hay atajo para saltarse la regla."""
    pago = fabrica_pago(ana, mensual, INICIO, VENCE, laura)
    with pytest.raises(DatosInvalidos):
        replace(pago, fecha_vencimiento=date(2027, 1, 4))


# Las tres pruebas de la guía: transición aceptada, transición inválida y frontera
def test_transicion_aceptada_vigente_a_anulado_conserva_la_identidad(
    ana, mensual, laura, carlos, fabrica_pago
):
    pago = fabrica_pago(ana, mensual, INICIO, VENCE, laura)
    identidad, ahora = pago.id, bogota(2026, 10, 7, 19, 0)
    pago.anular("  Plan equivocado ", carlos, ahora)
    assert (pago.id, pago.estado, pago.esta_vigente()) == (identidad, EstadoPago.ANULADO, False)
    assert (pago.anulado_por, pago.fecha_anulacion, pago.motivo_anulacion) == (
        carlos,
        ahora,
        "Plan equivocado",
    )


def test_transicion_invalida_anular_dos_veces_no_cambia_nada(
    ana, mensual, laura, carlos, fabrica_pago
):
    pago = fabrica_pago(ana, mensual, INICIO, VENCE, laura)
    pago.anular("Plan equivocado", carlos, bogota(2026, 10, 7, 19, 0))
    antes = (pago.estado, pago.anulado_por, pago.fecha_anulacion, pago.motivo_anulacion)
    with pytest.raises(PagoNoAnulable):
        pago.anular("Otro motivo", laura, bogota(2026, 10, 8, 9, 0))
    assert (pago.estado, pago.anulado_por, pago.fecha_anulacion, pago.motivo_anulacion) == antes


@pytest.mark.parametrize(
    ("hoy", "esperado"),
    [
        (date(2026, 11, 4), EstadoMembresia.ACTIVO),
        (VENCE, EstadoMembresia.ACTIVO),  # el día del vencimiento cuenta
        (date(2026, 11, 6), EstadoMembresia.VENCIDO),
    ],
)
def test_frontera_el_dia_del_vencimiento_todavia_entra(
    ana, mensual, laura, fabrica_pago, hoy, esperado
):
    pago = fabrica_pago(ana, mensual, INICIO, VENCE, laura)
    assert CalculadoraMembresia().estado_de([pago], hoy) == (esperado, VENCE)
    assert pago.periodo.cubre(hoy) is (esperado is EstadoMembresia.ACTIVO)


@pytest.mark.parametrize(
    ("hoy", "puede"),
    [(date(2026, 10, 7), True), (date(2026, 10, 8), False)],
)
def test_frontera_la_recepcionista_corrige_hasta_la_medianoche_de_bogota(
    ana, mensual, laura, fabrica_pago, hoy, puede
):
    # Registrado a las 23:59:59 del 7 de octubre en Bogotá (04:59:59 del 8 en UTC).
    pago = fabrica_pago(
        ana, mensual, INICIO, VENCE, laura, registrado_en=bogota(2026, 10, 7, 23, 59, 59)
    )
    if puede:
        RecepcionistaCorrigeSuDia().exigir(pago, laura, hoy)
    else:
        with pytest.raises(PermisoDenegado):
            RecepcionistaCorrigeSuDia().exigir(pago, laura, hoy)
