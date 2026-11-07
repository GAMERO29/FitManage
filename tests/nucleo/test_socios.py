"""CU-02 Registrar socio y CU-03 Consultar estado como casos de uso (paga DT-16, Guía 15).

Antes vivían dentro de los controladores HTTP y solo se podían probar con una petición completa.
"""

from datetime import date

import pytest
from fechas import bogota

from aplicacion.socios import ConsultaEstadoService, RegistroSocioService
from dominio.errores import DocumentoDuplicado, SocioNoEncontrado
from dominio.modelos import EstadoMembresia, MedioPago, TipoDocumento

AHORA = bogota(2026, 10, 7, 18, 2)


def registro(repos):
    return RegistroSocioService(repos["socios"], repos["reloj"])


def consulta(repos):
    return ConsultaEstadoService(repos["socios"], repos["pagos"], repos["reloj"])


def test_registra_al_socio_con_la_autorizacion_de_datos_en_este_momento(entorno):
    repos = entorno(AHORA)
    socio = registro(repos).registrar(
        TipoDocumento.CC, "1093111222", "  Jorge ", " Rincón  ", "3001112233"
    )
    assert (socio.nombres, socio.apellidos) == ("Jorge", "Rincón")
    assert socio.autorizacion_datos == AHORA
    assert repos["socios"].buscar_por_documento(TipoDocumento.CC, "1093111222") == socio


def test_un_documento_ya_registrado_es_documento_duplicado(entorno):
    repos = entorno(AHORA)
    with pytest.raises(DocumentoDuplicado):
        registro(repos).registrar(TipoDocumento.CC, "1090123456", "Otra", "Ana", "3000000009")


def test_el_mismo_numero_con_otro_tipo_de_documento_no_es_duplicado(entorno):
    socio = registro(entorno(AHORA)).registrar(
        TipoDocumento.CE, "1090123456", "Ana", "Pérez", "3000000005"
    )
    assert socio.tipo_documento is TipoDocumento.CE


def test_consulta_un_socio_sin_pagos(entorno, ana):
    resultado = consulta(entorno(AHORA)).consultar(TipoDocumento.CC, "1090123456")
    assert resultado.socio == ana
    assert (resultado.estado, resultado.vence, resultado.hoy) == (
        EstadoMembresia.SIN_MEMBRESIA,
        None,
        date(2026, 10, 7),
    )


def test_consulta_un_socio_activo_y_uno_vencido(entorno, ana, mensual, laura, fabrica_pago):
    vigente = fabrica_pago(
        ana, mensual, date(2026, 9, 20), date(2026, 10, 19), laura, MedioPago.EFECTIVO, None
    )
    repos = entorno(AHORA, vigente)
    activo = consulta(repos).consultar(TipoDocumento.CC, "1090123456")
    assert (activo.estado, activo.vence) == (EstadoMembresia.ACTIVO, date(2026, 10, 19))
    al_dia_siguiente = entorno(bogota(2026, 10, 20, 8, 0), vigente)
    vencido = consulta(al_dia_siguiente).consultar(TipoDocumento.CC, "1090123456")
    assert (vencido.estado, vencido.vence) == (EstadoMembresia.VENCIDO, date(2026, 10, 19))


def test_un_documento_que_no_existe_es_socio_no_encontrado(entorno):
    with pytest.raises(SocioNoEncontrado):
        consulta(entorno(AHORA)).consultar(TipoDocumento.CC, "1111111111")
