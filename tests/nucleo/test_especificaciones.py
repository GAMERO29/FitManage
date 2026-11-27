"""Software III, Guía 13: la especificación PUEDE_ANULAR, probada sin interfaz ni base.

PUEDE_ANULAR = EsAdministrador() | (LoRegistroQuienAnula() & RegistradoElMismoDia())
"""

from datetime import date

import pytest
from fechas import bogota

from dominio.especificaciones import (
    PUEDE_ANULAR,
    EsAdministrador,
    LoRegistroQuienAnula,
    RegistradoElMismoDia,
    SolicitudAnulacion,
)
from dominio.modelos import Rol, Usuario

HOY = date(2026, 10, 7)
OTRA = Usuario("Laura", "laura.b@demo.local", Rol.RECEPCIONISTA)  # se llama igual que Laura


@pytest.fixture
def pago_de_laura(ana, mensual, laura, fabrica_pago):
    def crear(registrado_en):
        return fabrica_pago(
            ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura, registrado_en=registrado_en
        )

    return crear


# Tabla de verdad de la conjunción, con quien pide = recepcionista
@pytest.mark.parametrize(
    ("es_suyo", "es_de_hoy", "puede"),
    [(True, True, True), (True, False, False), (False, True, False), (False, False, False)],
)
def test_tabla_de_verdad_de_la_conjuncion(laura, pago_de_laura, es_suyo, es_de_hoy, puede):
    pago = pago_de_laura(bogota(2026, 10, 7 if es_de_hoy else 6, 18, 0))
    solicitud = SolicitudAnulacion(pago, laura if es_suyo else OTRA, HOY)
    assert (LoRegistroQuienAnula() & RegistradoElMismoDia()).es_satisfecha_por(solicitud) is puede
    assert PUEDE_ANULAR.es_satisfecha_por(solicitud) is puede


def test_la_disyuncion_deja_al_administrador_anular_lo_de_otro_dia(carlos, pago_de_laura):
    solicitud = SolicitudAnulacion(pago_de_laura(bogota(2026, 9, 1, 8, 0)), carlos, HOY)
    assert PUEDE_ANULAR.es_satisfecha_por(solicitud)
    # Si alguien cambiara | por &, el administrador ya no podría:
    conjuncion = EsAdministrador() & (LoRegistroQuienAnula() & RegistradoElMismoDia())
    assert not conjuncion.es_satisfecha_por(solicitud)


@pytest.mark.parametrize(
    ("registrado_en", "puede"),
    [(bogota(2026, 10, 7, 23, 59, 59), True), (bogota(2026, 10, 8, 0, 0, 0), False)],
)
def test_frontera_de_medianoche_en_bogota(laura, pago_de_laura, registrado_en, puede):
    """23:59:59 del 7 en Bogotá son las 04:59:59 del 8 en UTC: cuenta el día de Bogotá."""
    solicitud = SolicitudAnulacion(pago_de_laura(registrado_en), laura, HOY)
    assert RegistradoElMismoDia().es_satisfecha_por(solicitud) is puede


def test_dos_personas_con_el_mismo_nombre_no_son_la_misma(laura, pago_de_laura):
    """El error que tenía la pantalla: comparaba `registradoPor === sesion.nombre`."""
    solicitud = SolicitudAnulacion(pago_de_laura(bogota(2026, 10, 7, 9, 0)), OTRA, HOY)
    assert OTRA.nombre == laura.nombre
    assert not PUEDE_ANULAR.es_satisfecha_por(solicitud)


def test_la_negacion_tambien_se_compone(laura, pago_de_laura):
    solicitud = SolicitudAnulacion(pago_de_laura(bogota(2026, 10, 7, 9, 0)), laura, HOY)
    assert (~EsAdministrador()).es_satisfecha_por(solicitud)
