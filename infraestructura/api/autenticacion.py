"""Inicio de sesión y renovación: credenciales con los hashers de Django y bloqueo de RF-09."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction

from dominio.acceso import PoliticaBloqueo
from dominio.modelos import ZONA_HORARIA
from infraestructura.api import tokens
from infraestructura.persistencia.models import RenovacionModelo, UsuarioModelo
from infraestructura.persistencia.repositorios import _a_usuario

# Hash de una clave que nadie conoce: compararla con correos inexistentes iguala los tiempos.
_HASH_FICTICIO = make_password("cuenta-que-no-existe")
POLITICA = PoliticaBloqueo()


@dataclass(frozen=True)
class Sesion:
    token_acceso: str
    token_renovacion: str
    rol: str


class CredencialesInvalidas(Exception):
    pass


class CuentaBloqueada(Exception):
    def __init__(self, segundos: int, hasta: datetime) -> None:
        super().__init__("Cuenta bloqueada")
        self.segundos = segundos
        self.hasta = hasta


def _abrir_sesion(cuenta: UsuarioModelo) -> Sesion:
    token, huella = tokens.nuevo_token_renovacion()
    RenovacionModelo.objects.create(
        usuario=cuenta, huella=huella, vence=tokens.ahora_real() + tokens.VIGENCIA_RENOVACION
    )
    usuario = _a_usuario(cuenta)
    return Sesion(tokens.emitir_acceso(usuario), token, usuario.rol.value)


def _bloqueo(cuenta: UsuarioModelo, ahora: datetime) -> CuentaBloqueada:
    hasta = cuenta.bloqueada_hasta.astimezone(ZONA_HORARIA)
    return CuentaBloqueada(POLITICA.segundos_restantes(hasta, ahora), hasta)


def iniciar_sesion(correo: str, clave: str, ahora: datetime) -> Sesion:
    """Los fallos se guardan aunque la respuesta sea un error: por eso se lanza fuera del atomic."""
    with transaction.atomic():
        cuenta = UsuarioModelo.objects.select_for_update().filter(correo__iexact=correo).first()
        resultado = _verificar(cuenta, clave, ahora)
        if resultado is None:
            return _abrir_sesion(cuenta)
    raise resultado


def _verificar(cuenta: UsuarioModelo | None, clave: str, ahora: datetime) -> Exception | None:
    if cuenta is None:
        check_password(clave, _HASH_FICTICIO)
        return CredencialesInvalidas()
    if POLITICA.esta_bloqueada(cuenta.bloqueada_hasta, ahora):
        return _bloqueo(cuenta, ahora)
    if cuenta.activo and check_password(clave, cuenta.clave_hash):
        cuenta.intentos_fallidos, cuenta.bloqueada_hasta = 0, None
        cuenta.save(update_fields=["intentos_fallidos", "bloqueada_hasta"])
        return None
    cuenta.intentos_fallidos, cuenta.bloqueada_hasta = POLITICA.registrar_fallo(
        cuenta.intentos_fallidos, ahora
    )
    cuenta.save(update_fields=["intentos_fallidos", "bloqueada_hasta"])
    return _bloqueo(cuenta, ahora) if cuenta.bloqueada_hasta else CredencialesInvalidas()


@transaction.atomic
def renovar(token_renovacion: str, ahora: datetime) -> Sesion:
    """Rota el token: el usado queda revocado. Una cuenta bloqueada o inactiva no renueva."""
    previa = (
        RenovacionModelo.objects.select_for_update()
        .select_related("usuario")
        .filter(
            huella=tokens.huella(token_renovacion), revocada=False, vence__gt=tokens.ahora_real()
        )
        .first()
    )
    if previa is None:
        raise CredencialesInvalidas()
    cuenta = previa.usuario
    previa.revocada = True
    previa.save(update_fields=["revocada"])
    if not cuenta.activo or POLITICA.esta_bloqueada(cuenta.bloqueada_hasta, ahora):
        raise CredencialesInvalidas()
    return _abrir_sesion(cuenta)
