from datetime import date
from uuid import uuid4

import pytest
from dobles import PagosEnMemoria, RelojFijo
from fechas import bogota

from aplicacion.pagos import AnulacionPagoService
from dominio.calculadora import CalculadoraMembresia
from dominio.errores import MotivoRequerido, PagoNoAnulable, PagoNoEncontrado, PermisoDenegado
from dominio.modelos import EstadoMembresia, EstadoPago, Rol, Usuario

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


def test_la_recepcionista_anula_lo_que_ella_registro_hoy(ana, mensual, laura, fabrica_pago):
    """ADR N.° 18: corrige un error en el momento."""
    pago = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    _, servicio = preparar(pago)
    assert servicio.anular_ultimo(ana, laura, "Plan equivocado") is pago


def test_la_recepcionista_no_anula_un_pago_de_ayer(ana, mensual, laura, fabrica_pago):
    _, servicio = preparar(fabrica_pago(ana, mensual, date(2026, 10, 6), date(2026, 11, 4), laura))
    with pytest.raises(PermisoDenegado):
        servicio.anular_ultimo(ana, laura, "Intento")


def test_la_recepcionista_no_anula_lo_que_registro_otra_persona(
    ana, mensual, laura, carlos, fabrica_pago
):
    _, servicio = preparar(fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), carlos))
    with pytest.raises(PermisoDenegado):
        servicio.anular_ultimo(ana, laura, "Intento")


def test_la_recepcionista_si_puede_preparar_un_cambio_de_plan_de_otro_dia(
    ana, mensual, laura, fabrica_pago
):
    pago = fabrica_pago(ana, mensual, date(2026, 9, 7), date(2026, 10, 6), laura)
    _, servicio = preparar(pago)
    assert servicio.verificar_anulable(pago.id, laura, para_cambio_de_plan=True) is pago


def test_otros_roles_no_anulan(ana, mensual, laura, fabrica_pago):
    entrenador = Usuario("Diego", "diego@gimnasio-demo.co", Rol.ENTRENADOR)
    _, servicio = preparar(fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura))
    with pytest.raises(PermisoDenegado):
        servicio.anular_ultimo(ana, entrenador, "Intento")


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


def test_anula_por_id_cuando_es_el_ultimo_pago_vigente(ana, mensual, laura, carlos, fabrica_pago):
    anterior = fabrica_pago(ana, mensual, date(2026, 9, 7), date(2026, 10, 6), laura)
    ultimo = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    _, servicio = preparar(anterior, ultimo)
    assert servicio.anular(ultimo.id, carlos, "Plan equivocado") is ultimo
    assert ultimo.estado is EstadoPago.ANULADO


def test_por_id_no_deja_anular_un_pago_que_no_es_el_ultimo(
    ana, mensual, laura, carlos, fabrica_pago
):
    anterior = fabrica_pago(ana, mensual, date(2026, 9, 7), date(2026, 10, 6), laura)
    ultimo = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    _, servicio = preparar(anterior, ultimo)
    with pytest.raises(PagoNoAnulable):
        servicio.anular(anterior.id, carlos, "Intento sobre el pago viejo")
    assert anterior.esta_vigente() and ultimo.esta_vigente()


def test_por_id_un_pago_ya_anulado_no_se_anula_dos_veces(ana, mensual, laura, carlos, fabrica_pago):
    pago = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    _, servicio = preparar(pago)
    servicio.anular(pago.id, carlos, "Primera vez")
    with pytest.raises(PagoNoAnulable):
        servicio.anular(pago.id, carlos, "Segunda vez")


def test_por_id_pago_inexistente(carlos):
    _, servicio = preparar()
    with pytest.raises(PagoNoEncontrado):
        servicio.anular(uuid4(), carlos, "No existe")


def test_por_id_la_recepcionista_no_anula_un_pago_viejo(ana, mensual, laura, fabrica_pago):
    pago = fabrica_pago(ana, mensual, date(2026, 9, 7), date(2026, 10, 6), laura)
    _, servicio = preparar(pago)
    with pytest.raises(PermisoDenegado):
        servicio.anular(pago.id, laura, "Intento")


@pytest.mark.parametrize(
    ("registrado_en", "ahora", "permitido"),
    [
        # Guía II-01, tabla de decisión: la frontera del «hoy» es la medianoche de Bogotá.
        (bogota(2026, 10, 6, 23, 59, 59), bogota(2026, 10, 7, 0, 0, 0), False),
        (bogota(2026, 10, 7, 0, 0, 0), bogota(2026, 10, 7, 23, 59, 59), True),
        # 7:30 p. m. en Bogotá ya es el 8 de octubre en UTC: el día se cuenta en Bogotá (RN-03).
        (bogota(2026, 10, 7, 19, 30), bogota(2026, 10, 7, 21, 0), True),
    ],
    ids=["un-segundo-antes-de-medianoche", "primer-segundo-del-dia", "noche-en-utc-es-otro-dia"],
)
def test_frontera_del_dia_para_la_recepcionista(
    ana, mensual, laura, fabrica_pago, registrado_en, ahora, permitido
):
    pago = fabrica_pago(
        ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura, registrado_en=registrado_en
    )
    servicio = AnulacionPagoService(PagosEnMemoria(pago), RelojFijo(ahora))
    if permitido:
        assert servicio.anular(pago.id, laura, "Plan equivocado") is pago
    else:
        with pytest.raises(PermisoDenegado):
            servicio.anular(pago.id, laura, "Plan equivocado")
        assert pago.esta_vigente()
