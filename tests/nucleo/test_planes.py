"""CambioPrecioService sin base de datos (CU-05, RN-08)."""

from decimal import Decimal

import pytest
from dobles import PlanesEnMemoria

from aplicacion.planes import CambioPrecioService
from dominio.errores import DatosInvalidos, PermisoDenegado, PlanNoDisponible
from dominio.modelos import Plan, Rol, Usuario

CARLOS = Usuario("Carlos", "carlos@gimnasio-demo.co", Rol.ADMINISTRADOR)
LAURA = Usuario("Laura", "laura@gimnasio-demo.co", Rol.RECEPCIONISTA)


@pytest.fixture
def mensual():
    return Plan("Mensual", 30, Decimal("75000"))


def test_el_administrador_cambia_el_precio(mensual):
    planes = PlanesEnMemoria(mensual)
    nuevo = CambioPrecioService(planes).cambiar_precio(mensual.id, Decimal("80000"), CARLOS)
    assert planes.obtener(mensual.id).precio == Decimal("80000") == nuevo.precio
    assert (nuevo.nombre, nuevo.duracion_dias) == ("Mensual", 30)


def test_solo_el_administrador_cambia_precios(mensual):
    with pytest.raises(PermisoDenegado):
        CambioPrecioService(PlanesEnMemoria(mensual)).cambiar_precio(
            mensual.id, Decimal("1"), LAURA
        )


def test_el_plan_debe_existir(mensual):
    with pytest.raises(PlanNoDisponible):
        CambioPrecioService(PlanesEnMemoria()).cambiar_precio(mensual.id, Decimal("1"), CARLOS)


def test_el_precio_no_puede_ser_cero(mensual):
    with pytest.raises(DatosInvalidos):
        CambioPrecioService(PlanesEnMemoria(mensual)).cambiar_precio(
            mensual.id, Decimal("0"), CARLOS
        )
