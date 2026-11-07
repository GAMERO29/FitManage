"""Guía 16: el primer arranque deja la base de producción lista para iniciar sesión."""

from io import StringIO

import pytest
from django.contrib.auth.hashers import check_password
from django.core.management import call_command
from django.core.management.base import CommandError

from infraestructura.persistencia.models import PlanModelo, UsuarioModelo

CLAVE = "una-clave-larga-de-prueba"


@pytest.fixture
def variables(monkeypatch):
    monkeypatch.setenv("FITMANAGE_ADMIN_NOMBRE", "Carlos")
    monkeypatch.setenv("FITMANAGE_ADMIN_CORREO", "Carlos@Gimnasio.co ")
    monkeypatch.setenv("FITMANAGE_ADMIN_CLAVE", CLAVE)


def preparar() -> str:
    salida = StringIO()
    call_command("preparar_gimnasio", stdout=salida)
    return salida.getvalue()


@pytest.mark.django_db
def test_crea_los_planes_y_el_administrador_una_sola_vez(variables):
    primera = preparar()
    segunda = preparar()
    assert PlanModelo.objects.count() == 4 and UsuarioModelo.objects.count() == 1
    admin = UsuarioModelo.objects.get()
    esperado = ("Carlos", "carlos@gimnasio.co", "ADMINISTRADOR")
    assert (admin.nombre, admin.correo, admin.rol) == esperado
    assert check_password(CLAVE, admin.clave_hash)
    assert "se creó la cuenta" in primera and "ya existe, no se toca" in segunda
    assert CLAVE not in primera + segunda


@pytest.mark.django_db
def test_no_toca_los_planes_ni_la_cuenta_que_ya_existen(variables):
    PlanModelo.objects.create(nombre="Mensual", duracion_dias=30, precio=90000)
    UsuarioModelo.objects.create(nombre="Dueña", correo="duena@gimnasio.co", rol="ADMINISTRADOR")
    preparar()
    assert list(PlanModelo.objects.values_list("precio", flat=True)) == [90000]
    assert list(UsuarioModelo.objects.values_list("nombre", flat=True)) == ["Dueña"]


@pytest.mark.django_db
def test_sin_variables_avisa_y_no_crea_ninguna_cuenta(monkeypatch):
    for nombre in ("FITMANAGE_ADMIN_NOMBRE", "FITMANAGE_ADMIN_CORREO", "FITMANAGE_ADMIN_CLAVE"):
        monkeypatch.delenv(nombre, raising=False)
    assert "Nadie podrá iniciar sesión" in preparar()
    assert not UsuarioModelo.objects.exists()


@pytest.mark.django_db
def test_rechaza_una_clave_corta_sin_mostrarla(variables, monkeypatch):
    monkeypatch.setenv("FITMANAGE_ADMIN_CLAVE", "corta123")
    with pytest.raises(CommandError) as error:
        preparar()
    assert "corta123" not in str(error.value)
    assert not UsuarioModelo.objects.exists() and not PlanModelo.objects.exists()


@pytest.mark.django_db
def test_no_convierte_en_administrador_una_cuenta_existente(variables):
    UsuarioModelo.objects.create(nombre="Laura", correo="carlos@gimnasio.co", rol="RECEPCIONISTA")
    with pytest.raises(CommandError):
        preparar()
    assert UsuarioModelo.objects.get().rol == "RECEPCIONISTA"
