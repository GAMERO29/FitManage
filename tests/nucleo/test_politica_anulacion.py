"""Software III, Guía 03: la política de anulación es intercambiable sin tocar el servicio."""

from datetime import date

import pytest
from dobles import PagosEnMemoria, RelojFijo
from fechas import bogota

from aplicacion.pagos import AnulacionPagoService
from dominio.errores import PermisoDenegado
from dominio.politicas import RecepcionistaCorrigeSuDia, SoloAdministradorAnula

AHORA = bogota(2026, 10, 7, 19, 0)
POLITICAS = [RecepcionistaCorrigeSuDia(), SoloAdministradorAnula()]


@pytest.mark.parametrize("politica", POLITICAS, ids=lambda p: type(p).__name__)
def test_toda_politica_deja_anular_al_administrador(
    politica, ana, mensual, laura, carlos, fabrica_pago
):
    """Cláusula común del contrato: el administrador siempre puede corregir."""
    pago = fabrica_pago(ana, mensual, date(2026, 9, 1), date(2026, 9, 30), laura)
    politica.exigir(pago, carlos, AHORA.date())  # no lanza


@pytest.mark.parametrize("politica", POLITICAS, ids=lambda p: type(p).__name__)
def test_ninguna_politica_deja_anular_lo_ajeno_de_otro_dia(
    politica, ana, mensual, laura, carlos, fabrica_pago
):
    """Cláusula común: la recepcionista nunca anula lo que otra persona registró otro día."""
    ajeno = fabrica_pago(ana, mensual, date(2026, 9, 1), date(2026, 9, 30), carlos)
    with pytest.raises(PermisoDenegado):
        politica.exigir(ajeno, laura, AHORA.date())


def test_la_variante_cambia_la_regla_sin_cambiar_el_servicio(ana, mensual, laura, fabrica_pago):
    """Con la regla anterior al ADR 18, ni lo suyo de hoy puede anular la recepcionista."""
    pago = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    vigente = AnulacionPagoService(PagosEnMemoria(pago), RelojFijo(AHORA))
    anterior = AnulacionPagoService(
        PagosEnMemoria(pago), RelojFijo(AHORA), politica=SoloAdministradorAnula()
    )
    with pytest.raises(PermisoDenegado):
        anterior.anular(pago.id, laura, "Plan equivocado")
    assert pago.esta_vigente()
    assert vigente.anular(pago.id, laura, "Plan equivocado") is pago
