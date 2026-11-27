"""Software III, Guía 06: suprimir los datos de un socio sin pagos, sin base de datos."""

from datetime import date

import pytest
from dobles import PagosEnMemoria, RelojFijo, SociosEnMemoria
from fechas import bogota

from aplicacion.socios import SupresionSocioService
from dominio.auditoria import TipoEvento
from dominio.errores import PermisoDenegado, SocioConPagos, SocioNoEncontrado
from dominio.modelos import TipoDocumento

AHORA = bogota(2026, 11, 27, 10, 0)


class EventosEnMemoria:
    def __init__(self) -> None:
        self.eventos = []

    def registrar(self, evento) -> None:
        self.eventos.append(evento)


def preparar(socio, *pagos):
    repo_pagos = PagosEnMemoria(*pagos)
    socios, eventos = SociosEnMemoria(socio, pagos=repo_pagos), EventosEnMemoria()
    servicio = SupresionSocioService(socios, repo_pagos, RelojFijo(AHORA), eventos)
    return socios, eventos, servicio


def test_el_administrador_suprime_un_socio_sin_pagos(ana, carlos):
    socios, eventos, servicio = preparar(ana)
    servicio.suprimir(TipoDocumento.CC, ana.numero_documento, carlos)
    assert socios.buscar_por_documento(TipoDocumento.CC, ana.numero_documento) is None
    (evento,) = eventos.eventos
    assert (evento.tipo, evento.entidad_id, evento.detalle) == (
        TipoEvento.SOCIO_SUPRIMIDO,
        ana.id,
        {},
    )


def test_con_un_pago_anulado_tampoco_se_suprime(ana, mensual, laura, carlos, fabrica_pago):
    """El pago anulado también es un registro contable: la regla mira todos los pagos."""
    pago = fabrica_pago(ana, mensual, date(2026, 11, 1), date(2026, 11, 30), laura)
    pago.anular("Se registró dos veces", carlos, AHORA)
    socios, eventos, servicio = preparar(ana, pago)
    with pytest.raises(SocioConPagos):
        servicio.suprimir(TipoDocumento.CC, ana.numero_documento, carlos)
    assert socios.buscar_por_documento(TipoDocumento.CC, ana.numero_documento) is ana
    assert eventos.eventos == []


def test_la_recepcionista_no_suprime(ana, laura):
    socios, _, servicio = preparar(ana)
    with pytest.raises(PermisoDenegado):
        servicio.suprimir(TipoDocumento.CC, ana.numero_documento, laura)
    assert socios.buscar_por_documento(TipoDocumento.CC, ana.numero_documento) is ana


def test_un_documento_sin_socio_es_no_encontrado(ana, carlos):
    _, _, servicio = preparar(ana)
    with pytest.raises(SocioNoEncontrado):
        servicio.suprimir(TipoDocumento.CC, "1090000099", carlos)
