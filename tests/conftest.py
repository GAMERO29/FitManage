from __future__ import annotations

import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dobles import PagosEnMemoria, PlanesEnMemoria, RelojFijo, SociosEnMemoria  # noqa: E402

from dominio.modelos import (  # noqa: E402
    MedioPago,
    Pago,
    Plan,
    Rol,
    Socio,
    TipoDocumento,
    Usuario,
)

AUTORIZACION = datetime(2026, 6, 8, 9, 14)


@pytest.fixture
def ana() -> Socio:
    return Socio(TipoDocumento.CC, "1090123456", "Ana", "Pérez", "3000000005", AUTORIZACION)


@pytest.fixture
def maria() -> Socio:
    return Socio(
        TipoDocumento.PPT,
        "25789456",
        "María Fernanda",
        "Gil",
        "3000000004",
        AUTORIZACION,
    )


@pytest.fixture
def mensual() -> Plan:
    return Plan("Mensual", 30, Decimal("80000"))


@pytest.fixture
def trimestral() -> Plan:
    return Plan("Trimestral", 90, Decimal("210000"))


@pytest.fixture
def diario() -> Plan:
    return Plan("Diario", 1, Decimal("8000"))


@pytest.fixture
def laura() -> Usuario:
    return Usuario("Laura", "laura@gimnasio.test", Rol.RECEPCIONISTA)


@pytest.fixture
def carlos() -> Usuario:
    return Usuario("Carlos", "carlos@gimnasio.test", Rol.ADMINISTRADOR)


def crear_pago(
    socio,
    plan,
    inicio: date,
    vence: date,
    usuario,
    medio=MedioPago.EFECTIVO,
    referencia=None,
    registrado_en: datetime | None = None,
) -> Pago:
    return Pago(
        socio=socio,
        plan_id=plan.id,
        valor=plan.precio,
        duracion_dias=plan.duracion_dias,
        medio=medio,
        referencia=referencia,
        fecha_inicio=inicio,
        fecha_vencimiento=vence,
        registrado_por=usuario,
        registrado_en=registrado_en or datetime.combine(inicio, datetime.min.time()),
    )


@pytest.fixture
def fabrica_pago():
    return crear_pago


@pytest.fixture
def entorno(ana, maria, mensual, trimestral, diario):
    """Repositorios en memoria con dos socios y tres planes."""

    def _crear(ahora: datetime, *pagos: Pago):
        return {
            "socios": SociosEnMemoria(ana, maria),
            "planes": PlanesEnMemoria(mensual, trimestral, diario),
            "pagos": PagosEnMemoria(*pagos),
            "reloj": RelojFijo(ahora),
        }

    return _crear
