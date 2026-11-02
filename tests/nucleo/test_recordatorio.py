"""RF-06 (CU-08): texto del recordatorio de WhatsApp, escrito con TDD (Guía 8, FPI-24).

Hoy el mensaje siempre dice «vence el dd/mm/aaaa», aunque la lista de vencimientos
muestra socios que vencen hoy o mañana. La recepcionista pidió que el mensaje lo diga así.
"""

from datetime import date

import pytest

from dominio.recordatorio import texto_recordatorio

HOY = date(2026, 10, 7)


def test_si_vence_hoy_el_mensaje_lo_dice():
    assert texto_recordatorio("Ana", HOY, HOY) == (
        "Hola Ana, te recordamos que tu membresía en el gimnasio vence hoy. "
        "Te esperamos para renovarla."
    )


def test_si_vence_manana_dice_manana_y_la_fecha():
    assert texto_recordatorio("Ana", date(2026, 10, 8), HOY) == (
        "Hola Ana, te recordamos que tu membresía en el gimnasio vence mañana, 08/10/2026. "
        "Te esperamos para renovarla."
    )


def test_si_faltan_varios_dias_dice_cuantos_y_la_fecha():
    assert texto_recordatorio("Ana", date(2026, 10, 21), HOY) == (
        "Hola Ana, te recordamos que tu membresía en el gimnasio vence en 14 días, "
        "el 21/10/2026. Te esperamos para renovarla."
    )


@pytest.mark.parametrize(
    ("nombres", "saludo"),
    [("María Fernanda", "Hola María,"), ("  ANA  ", "Hola Ana,"), ("josé luis", "Hola José,")],
)
def test_saluda_solo_con_el_primer_nombre_bien_escrito(nombres, saludo):
    assert texto_recordatorio(nombres, HOY, HOY).startswith(saludo)


def test_no_se_arma_recordatorio_para_una_membresia_ya_vencida():
    with pytest.raises(ValueError, match="ya venció"):
        texto_recordatorio("Ana", date(2026, 10, 6), HOY)
