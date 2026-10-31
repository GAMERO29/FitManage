"""Adaptadores ORM: mismo contrato que los dobles en memoria (LSP) y restricciones de la base.

Paga DT-02 y la parte de base de datos de DT-01.
"""

from datetime import date

import pytest
from django.db import IntegrityError
from dobles import PagosEnMemoria, PlanesEnMemoria, RelojFijo, SociosEnMemoria
from fechas import bogota

from aplicacion.pagos import RegistroPagoService
from dominio.errores import ReferenciaDuplicada
from dominio.modelos import MedioPago, Socio, SolicitudPago, TipoDocumento
from infraestructura.persistencia.repositorios import (
    PagoRepositorioORM,
    PlanRepositorioORM,
    SocioRepositorioORM,
)


@pytest.fixture(params=["memoria", "orm"])
def repos(request, ana, maria, mensual):
    """Los mismos escenarios contra los dobles y contra Django ORM."""
    if request.param == "memoria":
        return SociosEnMemoria(ana, maria), PlanesEnMemoria(mensual), PagosEnMemoria()
    request.getfixturevalue("db")
    socios, planes = SocioRepositorioORM(), PlanRepositorioORM()
    for socio in (ana, maria):
        socios.guardar(socio)
    planes.guardar(mensual)
    return socios, planes, PagoRepositorioORM()


def test_busca_socio_por_tipo_y_numero_de_documento(repos, ana):
    socios, _, _ = repos
    assert socios.buscar_por_documento(TipoDocumento.CC, "1090123456").id == ana.id
    assert socios.buscar_por_documento(TipoDocumento.CE, "1090123456") is None


def test_obtiene_el_plan_con_su_precio(repos, mensual):
    _, planes, _ = repos
    plan = planes.obtener(mensual.id)
    assert (plan.nombre, plan.duracion_dias, plan.precio) == ("Mensual", 30, mensual.precio)


def test_pago_guardado_aparece_entre_los_vigentes(repos, ana, mensual, laura, fabrica_pago):
    _, _, pagos = repos
    pago = fabrica_pago(
        ana,
        mensual,
        date(2026, 10, 7),
        date(2026, 11, 5),
        laura,
        MedioPago.NEQUI,
        "M555012",
        bogota(2026, 10, 7, 18, 2),
    )
    pagos.guardar(pago)
    [leido] = pagos.vigentes_de(ana)
    assert (leido.id, leido.fecha_vencimiento, leido.referencia) == (
        pago.id,
        date(2026, 11, 5),
        "M555012",
    )
    assert leido.registrado_en == bogota(2026, 10, 7, 18, 2)
    assert pagos.existe_referencia_vigente("M555012")


def test_pago_anulado_deja_de_ser_vigente_y_libera_la_referencia(
    repos, ana, mensual, laura, carlos, fabrica_pago
):
    _, _, pagos = repos
    pago = fabrica_pago(
        ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura, MedioPago.NEQUI, "M123456"
    )
    pagos.guardar(pago)
    pago.anular("Plan equivocado", carlos, bogota(2026, 10, 7, 19, 0))
    pagos.guardar(pago)
    assert pagos.vigentes_de(ana) == []
    assert not pagos.existe_referencia_vigente("M123456")


def test_el_caso_de_uso_funciona_igual_con_cualquier_adaptador(repos, ana, mensual, laura):
    socios, planes, pagos = repos
    servicio = RegistroPagoService(socios, planes, pagos, RelojFijo(bogota(2026, 10, 7, 18, 2)))
    pago = servicio.registrar_pago(
        SolicitudPago(TipoDocumento.CC, "1090123456", mensual.id, "EFECTIVO"), laura
    )
    assert [p.id for p in pagos.vigentes_de(ana)] == [pago.id]


@pytest.mark.django_db
def test_la_base_rechaza_dos_pagos_vigentes_con_la_misma_referencia(
    ana, maria, mensual, laura, fabrica_pago
):
    # DT-01: aunque la verificación previa falle (dos recepcionistas al tiempo), la base no cede.
    SocioRepositorioORM().guardar(ana)
    SocioRepositorioORM().guardar(maria)
    PlanRepositorioORM().guardar(mensual)
    pagos = PagoRepositorioORM()
    pagos.guardar(
        fabrica_pago(
            ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura, MedioPago.NEQUI, "M777"
        )
    )
    with pytest.raises(ReferenciaDuplicada):
        pagos.guardar(
            fabrica_pago(
                maria, mensual, date(2026, 10, 7), date(2026, 11, 5), laura, MedioPago.NEQUI, "M777"
            )
        )


@pytest.mark.django_db
def test_la_base_rechaza_dos_socios_con_el_mismo_documento(ana):
    SocioRepositorioORM().guardar(ana)
    gemelo = Socio(
        TipoDocumento.CC, "1090123456", "Otra", "Persona", "3000000001", bogota(2026, 6, 8, 9, 0)
    )
    with pytest.raises(IntegrityError):
        SocioRepositorioORM().guardar(gemelo)


@pytest.mark.django_db
def test_plan_inexistente_devuelve_none():
    from uuid import uuid4

    assert PlanRepositorioORM().obtener(uuid4()) is None


@pytest.mark.django_db
def test_otros_errores_de_integridad_no_se_disfrazan_de_comprobante_duplicado(
    monkeypatch, ana, mensual, laura, fabrica_pago
):
    from infraestructura.persistencia.models import PagoModelo

    def falla(*args, **kwargs):
        raise IntegrityError("violates foreign key constraint")

    monkeypatch.setattr(PagoModelo.objects, "update_or_create", falla)
    with pytest.raises(IntegrityError):
        PagoRepositorioORM().guardar(
            fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
        )
