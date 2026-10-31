"""Escenario QA-05: dos recepcionistas registran al tiempo la misma referencia (solo PostgreSQL)."""

import threading
from decimal import Decimal

import pytest
from django.db import connection, connections
from dobles import RelojFijo
from fechas import bogota

from aplicacion.pagos import RegistroPagoService
from dominio.errores import ReferenciaDuplicada
from dominio.modelos import Plan, Rol, Socio, SolicitudPago, TipoDocumento, Usuario
from infraestructura.persistencia.models import PagoModelo
from infraestructura.persistencia.repositorios import (
    PagoRepositorioORM,
    PlanRepositorioORM,
    SocioRepositorioORM,
    UsuarioRepositorioORM,
)

REPETICIONES = 100

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(connection.vendor != "postgresql", reason="QA-05 se mide en PostgreSQL"),
]


class PagosConCarrera(PagoRepositorioORM):
    """Obliga a las dos recepcionistas a pasar la verificación previa en el mismo instante."""

    def __init__(self, barrera: threading.Barrier) -> None:
        self._barrera = barrera

    def existe_referencia_vigente(self, referencia: str) -> bool:
        self._barrera.wait(timeout=10)
        return super().existe_referencia_vigente(referencia)


def test_qa05_nunca_quedan_dos_pagos_vigentes_con_la_misma_referencia():
    plan = Plan("Mensual", 30, Decimal("80000"))
    PlanRepositorioORM().guardar(plan)
    recepcionistas = [
        Usuario("Laura", "laura@gimnasio.test", Rol.RECEPCIONISTA),
        Usuario("Diana", "diana@gimnasio.test", Rol.RECEPCIONISTA),
    ]
    for usuario in recepcionistas:
        UsuarioRepositorioORM().guardar(usuario)
    rechazos = 0
    rechazados_por_la_base: list[str] = []
    for i in range(REPETICIONES):
        socios = [
            Socio(
                TipoDocumento.CC,
                f"20{i:06d}{k}",
                "Socio",
                "Prueba",
                "3000000000",
                bogota(2026, 6, 8, 9, 0),
            )
            for k in (1, 2)
        ]
        for socio in socios:
            SocioRepositorioORM().guardar(socio)
        barrera = threading.Barrier(2)
        resultados: list[str] = []

        def registrar(socio, usuario, barrera=barrera, resultados=resultados, ref=f"N{i:04d}"):
            servicio = RegistroPagoService(
                SocioRepositorioORM(),
                PlanRepositorioORM(),
                PagosConCarrera(barrera),
                RelojFijo(bogota(2026, 10, 7, 18, 30)),
            )
            try:
                servicio.registrar_pago(
                    SolicitudPago(TipoDocumento.CC, socio.numero_documento, plan.id, "NEQUI", ref),
                    usuario,
                )
                resultados.append("guardado")
            except ReferenciaDuplicada as error:
                resultados.append("rechazado")
                if error.__cause__ is not None:
                    rechazados_por_la_base.append(ref)
            finally:
                connections.close_all()

        hilos = [
            threading.Thread(target=registrar, args=(s, u))
            for s, u in zip(socios, recepcionistas, strict=True)
        ]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()
        assert sorted(resultados) == ["guardado", "rechazado"]
        assert PagoModelo.objects.filter(referencia=f"N{i:04d}", estado="VIGENTE").count() == 1
        rechazos += 1
    assert rechazos == REPETICIONES
    print(f"QA-05: {len(rechazados_por_la_base)} de {REPETICIONES} rechazos los hizo PostgreSQL")
