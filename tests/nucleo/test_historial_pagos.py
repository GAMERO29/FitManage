"""Software III, Guía 11: el agregado HistorialPagos protege I-1 e I-2 como unidad."""

from datetime import date

import pytest
from fechas import bogota

from dominio.errores import PagoNoAnulable
from dominio.historial import HistorialPagos
from dominio.modelos import EstadoMembresia


@pytest.fixture
def dos_pagos(ana, mensual, laura, fabrica_pago):
    """Octubre y, por renovación anticipada, noviembre (RN-04)."""
    octubre = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    noviembre = fabrica_pago(
        ana,
        mensual,
        date(2026, 11, 6),
        date(2026, 12, 5),
        laura,
        registrado_en=bogota(2026, 11, 2, 9, 0),
    )
    return octubre, noviembre


# Transición: anular el último deja como último al anterior y la membresía se recalcula
def test_anular_el_ultimo_hace_ultimo_al_anterior(ana, carlos, dos_pagos):
    octubre, noviembre = dos_pagos
    historial = HistorialPagos(ana, [octubre, noviembre])
    historial.exigir_que_sea_el_ultimo(noviembre)
    noviembre.anular("Pago duplicado", carlos, bogota(2026, 11, 2, 10, 0))
    assert historial.ultimo_vigente() is octubre
    assert historial.estado(date(2026, 11, 10)) == (EstadoMembresia.VENCIDO, date(2026, 11, 5))


# Límite: dos pagos que inician el mismo día; manda el que se registró después
def test_con_el_mismo_inicio_el_ultimo_es_el_registrado_despues(ana, mensual, laura, fabrica_pago):
    temprano = fabrica_pago(
        ana,
        mensual,
        date(2026, 10, 7),
        date(2026, 11, 5),
        laura,
        registrado_en=bogota(2026, 10, 7, 8, 0),
    )
    tarde = fabrica_pago(
        ana,
        mensual,
        date(2026, 10, 7),
        date(2026, 11, 5),
        laura,
        registrado_en=bogota(2026, 10, 7, 8, 1),
    )
    assert HistorialPagos(ana, [tarde, temprano]).ultimo_vigente() is tarde


# Intento inválido: anular uno que no es el último no cambia nada
def test_no_se_anula_un_pago_que_no_es_el_ultimo(ana, dos_pagos):
    octubre, noviembre = dos_pagos
    with pytest.raises(PagoNoAnulable, match="último pago vigente"):
        HistorialPagos(ana, [octubre, noviembre]).exigir_que_sea_el_ultimo(octubre)
    assert octubre.esta_vigente() and noviembre.esta_vigente()


def test_un_pago_ya_anulado_no_pasa_la_revision(ana, carlos, dos_pagos):
    octubre, noviembre = dos_pagos
    noviembre.anular("Pago duplicado", carlos, bogota(2026, 11, 2, 10, 0))
    with pytest.raises(PagoNoAnulable, match="ya está anulado"):
        HistorialPagos(ana, [octubre, noviembre]).exigir_que_sea_el_ultimo(noviembre)


# I-2: los periodos vigentes no se solapan
@pytest.mark.parametrize(
    ("hoy", "inicia"),
    [
        (date(2026, 11, 2), date(2026, 12, 6)),  # activo: después del vencimiento más lejano
        (date(2026, 12, 5), date(2026, 12, 6)),  # el día que vence también es renovación
        (date(2026, 12, 9), date(2026, 12, 9)),  # vencido: empieza hoy
    ],
)
def test_el_siguiente_periodo_no_se_solapa_con_los_vigentes(ana, dos_pagos, hoy, inicia):
    historial = HistorialPagos(ana, dos_pagos)
    siguiente = historial.periodo_del_siguiente(hoy, 30)
    assert siguiente.inicia == inicia
    assert all(not p.periodo.cubre(siguiente.inicia) for p in historial.vigentes)


def test_el_historial_ignora_pagos_de_otro_socio(ana, maria, mensual, laura, fabrica_pago):
    de_maria = fabrica_pago(maria, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    assert HistorialPagos(ana, [de_maria]).ultimo_vigente() is None
