"""Acceso del personal: bloqueo tras 5 intentos (RF-09, PA-10) y restablecimiento de clave."""

from datetime import timedelta
from uuid import uuid4

import pytest
from dobles import CorreoEnMemoria, UsuariosEnMemoria
from fechas import bogota

from aplicacion.acceso import RestablecimientoClaveService
from dominio.acceso import PoliticaBloqueo
from dominio.errores import (
    CorreoNoDisponible,
    DatosInvalidos,
    PermisoDenegado,
    UsuarioNoEncontrado,
)

AHORA = bogota(2026, 10, 7, 21, 10)


@pytest.mark.parametrize("fallos_previos", [0, 1, 2, 3])
def test_los_primeros_cuatro_fallos_no_bloquean(fallos_previos):
    intentos, bloqueada_hasta = PoliticaBloqueo().registrar_fallo(fallos_previos, AHORA)
    assert intentos == fallos_previos + 1
    assert bloqueada_hasta is None


def test_el_quinto_fallo_bloquea_15_minutos():
    intentos, bloqueada_hasta = PoliticaBloqueo().registrar_fallo(4, AHORA)
    assert intentos == 5
    assert bloqueada_hasta == AHORA + timedelta(minutes=15)


def test_la_cuenta_se_desbloquea_sola_al_cumplirse_el_plazo():
    politica = PoliticaBloqueo()
    hasta = AHORA + timedelta(minutes=15)
    assert politica.esta_bloqueada(hasta, AHORA + timedelta(minutes=14, seconds=59))
    assert not politica.esta_bloqueada(hasta, hasta)
    assert not politica.esta_bloqueada(None, AHORA)


def test_segundos_restantes_para_el_desbloqueo():
    politica = PoliticaBloqueo()
    assert politica.segundos_restantes(AHORA + timedelta(minutes=15), AHORA) == 900
    assert politica.segundos_restantes(None, AHORA) == 0


def test_rechaza_fechas_sin_zona_horaria():
    with pytest.raises(DatosInvalidos):
        PoliticaBloqueo().registrar_fallo(0, AHORA.replace(tzinfo=None))


def servicio(correo=None, *usuarios):
    correo = correo or CorreoEnMemoria()
    enlaces = lambda u: f"https://fitmanage.test/restablecer/{u.id}/"  # noqa: E731
    return correo, RestablecimientoClaveService(UsuariosEnMemoria(*usuarios), correo, enlaces)


def test_el_administrador_envia_el_enlace_al_correo_de_la_cuenta(laura, carlos):
    correo, srv = servicio(None, laura, carlos)
    destino = srv.restablecer(laura.id, solicitante=carlos)
    assert destino is laura
    [mensaje] = correo.enviados
    assert mensaje.destinatario == "laura@gimnasio.test"
    assert f"/restablecer/{laura.id}/" in mensaje.cuerpo
    assert "30 minutos" in mensaje.cuerpo


def test_la_recepcionista_no_puede_restablecer_otra_cuenta(laura, carlos):
    correo, srv = servicio(None, laura, carlos)
    with pytest.raises(PermisoDenegado):
        srv.restablecer(carlos.id, solicitante=laura)
    assert correo.enviados == []


def test_cuenta_inexistente(carlos):
    _, srv = servicio(None, carlos)
    with pytest.raises(UsuarioNoEncontrado):
        srv.restablecer(uuid4(), solicitante=carlos)


def test_si_el_correo_falla_el_error_sube_sin_tocar_la_cuenta(laura, carlos):
    correo = CorreoEnMemoria(falla=True)
    _, srv = servicio(correo, laura, carlos)
    with pytest.raises(CorreoNoDisponible):
        srv.restablecer(laura.id, solicitante=carlos)
    assert correo.enviados == []
