from datetime import date

import pytest
from fechas import bogota

from dominio.errores import (
    MedioPagoInvalido,
    PlanNoDisponible,
    ReferenciaDuplicada,
    ReferenciaRequerida,
    SocioNoEncontrado,
)
from dominio.modelos import EstadoPago, MedioPago, SolicitudPago, TipoDocumento
from aplicacion.pagos import RegistroPagoService

AHORA = bogota(2026, 10, 7, 18, 2)


def servicio(repos):
    return RegistroPagoService(repos["socios"], repos["planes"], repos["pagos"], repos["reloj"])


def solicitud(plan, medio="EFECTIVO", referencia=None, tipo=TipoDocumento.CC, numero="1090123456"):
    return SolicitudPago(tipo, numero, plan.id, medio, referencia)


def test_registra_pago_en_efectivo_sin_referencia(entorno, mensual, laura):
    repos = entorno(AHORA)
    pago = servicio(repos).registrar_pago(solicitud(mensual), laura)
    assert pago.medio is MedioPago.EFECTIVO and pago.referencia is None
    assert (pago.fecha_inicio, pago.fecha_vencimiento) == (
        date(2026, 10, 7),
        date(2026, 11, 5),
    )
    assert pago.estado is EstadoPago.VIGENTE
    assert repos["pagos"].todos() == [pago]


def test_el_pago_copia_valor_y_duracion_del_plan(entorno, mensual, laura):
    pago = servicio(entorno(AHORA)).registrar_pago(solicitud(mensual), laura)
    assert pago.valor == mensual.precio and pago.duracion_dias == 30


def test_el_pago_guarda_quien_lo_registro_y_cuando(entorno, mensual, laura):
    pago = servicio(entorno(AHORA)).registrar_pago(solicitud(mensual), laura)
    assert pago.registrado_por == laura and pago.registrado_en == AHORA


def test_trimestral_desde_el_primero_de_marzo_vence_el_29_de_mayo(entorno, trimestral, laura):
    repos = entorno(bogota(2026, 3, 1, 8, 0))
    pago = servicio(repos).registrar_pago(solicitud(trimestral), laura)
    assert pago.fecha_vencimiento == date(2026, 5, 29)


def test_plan_diario_vence_el_mismo_dia(entorno, diario, laura):
    pago = servicio(entorno(AHORA)).registrar_pago(solicitud(diario), laura)
    assert pago.fecha_inicio == pago.fecha_vencimiento == date(2026, 10, 7)


def test_renovacion_anticipada_no_pierde_dias(entorno, ana, mensual, laura, fabrica_pago):
    vigente = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    repos = entorno(bogota(2026, 11, 1, 9, 0), vigente)
    pago = servicio(repos).registrar_pago(solicitud(mensual), laura)
    assert pago.fecha_inicio == date(2026, 11, 6)


def test_pago_digital_exige_referencia(entorno, mensual, laura):
    with pytest.raises(ReferenciaRequerida):
        servicio(entorno(AHORA)).registrar_pago(solicitud(mensual, "NEQUI", "   "), laura)


def test_referencia_se_guarda_sin_espacios(entorno, mensual, laura):
    pago = servicio(entorno(AHORA)).registrar_pago(solicitud(mensual, "nequi", " M555012 "), laura)
    assert pago.medio is MedioPago.NEQUI and pago.referencia == "M555012"


def test_referencia_duplicada_en_pago_vigente_se_rechaza(
    entorno, ana, maria, mensual, laura, fabrica_pago
):
    # CP-03c
    previo = fabrica_pago(
        maria,
        mensual,
        date(2026, 9, 16),
        date(2026, 10, 15),
        laura,
        MedioPago.NEQUI,
        "M123456",
    )
    with pytest.raises(ReferenciaDuplicada):
        servicio(entorno(AHORA, previo)).registrar_pago(
            solicitud(mensual, "NEQUI", "M123456"), laura
        )


def test_referencia_de_un_pago_anulado_se_puede_reutilizar(
    entorno, maria, mensual, laura, carlos, fabrica_pago
):
    # CP-10d
    anulado = fabrica_pago(
        maria,
        mensual,
        date(2026, 9, 16),
        date(2026, 10, 15),
        laura,
        MedioPago.NEQUI,
        "M123456",
    )
    anulado.anular("Socio equivocado", carlos, bogota(2026, 9, 16, 19, 0))
    pago = servicio(entorno(AHORA, anulado)).registrar_pago(
        solicitud(mensual, "NEQUI", "M123456"), laura
    )
    assert pago.referencia == "M123456"


def test_socio_inexistente_se_rechaza(entorno, mensual, laura):
    with pytest.raises(SocioNoEncontrado):
        servicio(entorno(AHORA)).registrar_pago(solicitud(mensual, numero="1111111111"), laura)


def test_mismo_numero_con_otro_tipo_de_documento_no_es_el_mismo_socio(entorno, mensual, laura):
    with pytest.raises(SocioNoEncontrado):
        servicio(entorno(AHORA)).registrar_pago(solicitud(mensual, tipo=TipoDocumento.CE), laura)


def test_plan_desactivado_no_se_usa_en_pagos_nuevos(entorno, mensual, laura):
    # CP-02a
    mensual.desactivar()
    with pytest.raises(PlanNoDisponible):
        servicio(entorno(AHORA)).registrar_pago(solicitud(mensual), laura)


def test_medio_de_pago_inexistente_se_rechaza(entorno, mensual, laura):
    with pytest.raises(MedioPagoInvalido):
        servicio(entorno(AHORA)).registrar_pago(solicitud(mensual, "BITCOIN"), laura)
