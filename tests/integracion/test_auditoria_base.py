"""Guía II-03, ítem I-4 (#59): la base protege el rastro y la coherencia de la anulación.

Corre en SQLite (local) y en PostgreSQL (job `artefacto`): la migración 0003 crea el disparador
de cada motor.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

import pytest
from django.db import DatabaseError, IntegrityError, transaction
from django.utils import timezone

from infraestructura.persistencia.models import (
    EventoAuditoriaModelo,
    PagoModelo,
    PlanModelo,
    SocioModelo,
    UsuarioModelo,
)

pytestmark = pytest.mark.django_db
AHORA = datetime(2026, 11, 10, 9, 0, tzinfo=timezone.get_fixed_timezone(-300))


@pytest.fixture
def evento():
    return EventoAuditoriaModelo.objects.create(
        ocurrido_en=AHORA,
        tipo="PAGO_ANULADO",
        actor_nombre="Carlos Demo",
        entidad_id=uuid.uuid4(),
        detalle={"motivo": "Plan equivocado"},
    )


def test_la_auditoria_acepta_inserciones(evento):
    assert EventoAuditoriaModelo.objects.filter(id=evento.id).exists()


def test_la_base_rechaza_modificar_un_evento(evento):
    with pytest.raises(DatabaseError), transaction.atomic():
        EventoAuditoriaModelo.objects.filter(id=evento.id).update(detalle={"motivo": "otro"})
    evento.refresh_from_db()
    assert evento.detalle == {"motivo": "Plan equivocado"}


def test_la_base_rechaza_borrar_un_evento(evento):
    with pytest.raises(DatabaseError), transaction.atomic():
        EventoAuditoriaModelo.objects.filter(id=evento.id).delete()
    assert EventoAuditoriaModelo.objects.filter(id=evento.id).exists()


@pytest.fixture
def base_de_pago():
    usuario = UsuarioModelo.objects.create(
        nombre="Laura Demo", correo="laura@demo.test", rol="RECEPCIONISTA"
    )
    socio = SocioModelo.objects.create(
        tipo_documento="CC",
        numero_documento="1090000011",
        nombres="Ana",
        apellidos="Prueba Demo",
        telefono="3001234567",
        autorizacion_datos=AHORA,
    )
    plan = PlanModelo.objects.create(nombre="Mensual", duracion_dias=30, precio=Decimal("75000"))
    return {
        "socio": socio,
        "plan": plan,
        "valor": Decimal("75000"),
        "duracion_dias": 30,
        "medio": "EFECTIVO",
        "fecha_inicio": date(2026, 11, 10),
        "fecha_vencimiento": date(2026, 12, 9),
        "registrado_por": usuario,
        "registrado_en": AHORA,
    }


@pytest.mark.parametrize(
    "cambios",
    [
        {"estado": "BORRADO"},
        {"estado": "ANULADO"},  # anulado sin motivo, sin autor y sin fecha
        {"estado": "ANULADO", "motivo_anulacion": "", "fecha_anulacion": AHORA},
        {"estado": "VIGENTE", "fecha_anulacion": AHORA},  # vigente con rastro de anulación
    ],
    ids=["estado-inventado", "anulado-vacio", "anulado-sin-motivo", "vigente-con-fecha"],
)
def test_la_base_rechaza_un_pago_incoherente(base_de_pago, cambios):
    with pytest.raises(IntegrityError), transaction.atomic():
        PagoModelo.objects.create(**base_de_pago, **cambios)


def test_un_pago_anulado_completo_se_acepta(base_de_pago):
    pago = PagoModelo.objects.create(
        **base_de_pago,
        estado="ANULADO",
        fecha_anulacion=AHORA,
        anulado_por=base_de_pago["registrado_por"],
        motivo_anulacion="Plan equivocado",
    )
    assert pago.estado == "ANULADO"


# Software III, Guía 14 (ADR N.° 20, DEF-03): TRUNCATE tampoco vacía el rastro. Solo PostgreSQL:
# SQLite no tiene TRUNCATE y su DELETE sin condición ya lo frena el disparador de fila.
solo_postgres = pytest.mark.skipif(
    "postgresql" not in __import__("os").environ.get("DATABASE_URL", ""),
    reason="TRUNCATE solo existe en PostgreSQL",
)


def _truncar_con(ajuste: str) -> None:
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SET CONSTRAINTS ALL IMMEDIATE"
        )  # las llaves diferidas del evento recién creado
        cursor.execute("SET LOCAL fitmanage.permitir_vaciado = %s", [ajuste])
        cursor.execute("TRUNCATE auditoria")


@solo_postgres
def test_la_base_rechaza_vaciar_la_auditoria_con_truncate(evento):
    with pytest.raises(DatabaseError, match="no se puede vaciar"), transaction.atomic():
        _truncar_con("no")
    assert EventoAuditoriaModelo.objects.filter(id=evento.id).exists()


@solo_postgres
def test_solo_la_sesion_de_las_pruebas_puede_vaciarla(evento):
    """Es lo que usa pytest-django entre pruebas con transacciones reales (conftest.py)."""
    with transaction.atomic():
        _truncar_con("si")
        assert not EventoAuditoriaModelo.objects.exists()
