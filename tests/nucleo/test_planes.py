"""GestionPlanesService sin base de datos (CU-05, RN-08, RN-09)."""

from decimal import Decimal

import pytest
from dobles import PlanesEnMemoria

from aplicacion.planes import GestionPlanesService
from dominio.errores import (
    DatosInvalidos,
    PermisoDenegado,
    PlanDuplicado,
    PlanNoDisponible,
    UltimoPlanActivo,
)
from dominio.modelos import Plan, Rol, Usuario
from dominio.puertos import SinAuditoria

CARLOS = Usuario("Carlos", "carlos@gimnasio-demo.co", Rol.ADMINISTRADOR)
LAURA = Usuario("Laura", "laura@gimnasio-demo.co", Rol.RECEPCIONISTA)


@pytest.fixture
def mensual():
    return Plan("Mensual", 30, Decimal("75000"))


@pytest.fixture
def diario():
    return Plan("Diario", 1, Decimal("8000"))


def test_el_administrador_cambia_el_precio(mensual):
    planes = PlanesEnMemoria(mensual)
    nuevo = GestionPlanesService(planes).cambiar(mensual.id, CARLOS, precio=Decimal("80000"))
    assert planes.obtener(mensual.id).precio == Decimal("80000") == nuevo.precio
    assert (nuevo.nombre, nuevo.duracion_dias, nuevo.activo) == ("Mensual", 30, True)


def test_solo_el_administrador_gestiona_planes(mensual):
    servicio = GestionPlanesService(PlanesEnMemoria(mensual))
    with pytest.raises(PermisoDenegado):
        servicio.cambiar(mensual.id, LAURA, precio=Decimal("1"))
    with pytest.raises(PermisoDenegado):
        servicio.crear("Semestral", 180, Decimal("380000"), LAURA)


def test_el_plan_debe_existir(mensual):
    with pytest.raises(PlanNoDisponible):
        GestionPlanesService(PlanesEnMemoria()).cambiar(mensual.id, CARLOS, precio=Decimal("1"))


def test_el_precio_no_puede_ser_cero(mensual):
    with pytest.raises(DatosInvalidos):
        GestionPlanesService(PlanesEnMemoria(mensual)).cambiar(
            mensual.id, CARLOS, precio=Decimal("0")
        )


def test_crear_un_plan_nuevo_queda_activo(mensual):
    planes = PlanesEnMemoria(mensual)
    plan = GestionPlanesService(planes).crear("  Semestral  ", 180, Decimal("380000"), CARLOS)
    assert (plan.nombre, plan.activo) == ("Semestral", True)
    assert planes.obtener(plan.id) == plan


def test_no_se_repite_el_nombre_aunque_cambien_las_mayusculas(mensual):
    with pytest.raises(PlanDuplicado):
        GestionPlanesService(PlanesEnMemoria(mensual)).crear(
            "MENSUAL", 31, Decimal("70000"), CARLOS
        )


def test_un_plan_sin_duracion_no_se_crea(mensual):
    with pytest.raises(DatosInvalidos):
        GestionPlanesService(PlanesEnMemoria(mensual)).crear("Gratis", 0, Decimal("1"), CARLOS)


def test_desactivar_y_volver_a_activar(mensual, diario):
    planes = PlanesEnMemoria(mensual, diario)
    servicio = GestionPlanesService(planes)
    assert servicio.cambiar(diario.id, CARLOS, activo=False).activo is False
    assert planes.obtener(diario.id).precio == Decimal("8000")
    assert servicio.cambiar(diario.id, CARLOS, activo=True).activo is True


def test_no_se_desactiva_el_unico_plan_activo(mensual, diario):
    planes = PlanesEnMemoria(mensual, diario)
    servicio = GestionPlanesService(planes)
    servicio.cambiar(diario.id, CARLOS, activo=False)
    with pytest.raises(UltimoPlanActivo):
        servicio.cambiar(mensual.id, CARLOS, activo=False)


def test_desactivar_un_plan_ya_inactivo_no_cuenta_como_el_ultimo(mensual, diario):
    planes = PlanesEnMemoria(mensual, diario)
    servicio = GestionPlanesService(planes)
    servicio.cambiar(diario.id, CARLOS, activo=False)
    assert servicio.cambiar(diario.id, CARLOS, activo=False).activo is False


def test_auditoria_sin_reloj_es_un_error_de_composicion():
    """Guía II-04: la única línea de `aplicacion/` sin cubrir. Sin reloj no hay fecha del evento."""
    with pytest.raises(ValueError, match="reloj"):
        GestionPlanesService(PlanesEnMemoria(), auditoria=SinAuditoria())


# --- Software III, Guía 05: la regla de qué planes se ven vive en el servicio, no en la vista ---


def test_la_lista_ofrece_solo_los_activos_ordenados_por_duracion(mensual, diario):
    viejo = Plan("Semestral", 180, Decimal("380000"), activo=False)
    servicio = GestionPlanesService(PlanesEnMemoria(mensual, viejo, diario))
    assert [p.nombre for p in servicio.listar(LAURA)] == ["Diario", "Mensual"]


def test_solo_el_administrador_ve_los_planes_desactivados(mensual):
    viejo = Plan("Semestral", 180, Decimal("380000"), activo=False)
    servicio = GestionPlanesService(PlanesEnMemoria(mensual, viejo))
    assert [p.nombre for p in servicio.listar(CARLOS, incluir_inactivos=True)] == [
        "Mensual",
        "Semestral",
    ]
    with pytest.raises(PermisoDenegado):
        servicio.listar(LAURA, incluir_inactivos=True)


def test_los_nombres_incluyen_los_planes_desactivados(mensual):
    viejo = Plan("Semestral", 180, Decimal("380000"), activo=False)
    nombres = GestionPlanesService(PlanesEnMemoria(mensual, viejo)).nombres()
    assert nombres == {mensual.id: "Mensual", viejo.id: "Semestral"}
