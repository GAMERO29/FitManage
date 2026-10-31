from datetime import date

import pytest
from dobles import PagosEnMemoria, RelojFijo
from fechas import bogota

from dominio.calculadora import CalculadoraMembresia
from dominio.errores import MotivoRequerido, PagoNoAnulable, PermisoDenegado
from dominio.modelos import EstadoMembresia, EstadoPago
from aplicacion.pagos import AnulacionPagoService

AHORA = bogota(2026, 10, 7, 19, 0)


def preparar(*pagos):
    repo = PagosEnMemoria(*pagos)
    return repo, AnulacionPagoService(repo, RelojFijo(AHORA))


def test_administrador_anula_el_ultimo_pago_vigente(ana, mensual, laura, carlos, fabrica_pago):
    anterior = fabrica_pago(ana, mensual, date(2026, 9, 7), date(2026, 10, 6), laura)
    ultimo = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    _, servicio = preparar(anterior, ultimo)
    anulado = servicio.anular_ultimo(ana, carlos, "Se registró el plan equivocado")
    assert anulado is ultimo and ultimo.estado is EstadoPago.ANULADO
    assert anterior.esta_vigente()


def test_recepcionista_no_puede_anular(ana, mensual, laura, fabrica_pago):
    _, servicio = preparar(fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura))
    with pytest.raises(PermisoDenegado):
        servicio.anular_ultimo(ana, laura, "Intento")


def test_sin_pagos_vigentes_no_hay_nada_que_anular(ana, carlos):
    _, servicio = preparar()
    with pytest.raises(PagoNoAnulable):
        servicio.anular_ultimo(ana, carlos, "Error")


def test_anulacion_sin_motivo_se_rechaza(ana, mensual, laura, carlos, fabrica_pago):
    _, servicio = preparar(fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura))
    with pytest.raises(MotivoRequerido):
        servicio.anular_ultimo(ana, carlos, "")


def test_el_pago_anulado_no_se_borra(ana, mensual, laura, carlos, fabrica_pago):
    pago = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    repo, servicio = preparar(pago)
    servicio.anular_ultimo(ana, carlos, "Error de digitación")
    assert repo.todos() == [pago] and pago.fecha_anulacion == AHORA


def test_la_membresia_se_recalcula_tras_anular(ana, mensual, laura, carlos, fabrica_pago):
    anterior = fabrica_pago(ana, mensual, date(2026, 9, 7), date(2026, 10, 6), laura)
    ultimo = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    repo, servicio = preparar(anterior, ultimo)
    servicio.anular_ultimo(ana, carlos, "Plan equivocado")
    estado, vence = CalculadoraMembresia().estado_de(repo.vigentes_de(ana), date(2026, 10, 7))
    assert (estado, vence) == (EstadoMembresia.VENCIDO, date(2026, 10, 6))
