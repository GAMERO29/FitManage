"""Cuentas del personal (CU-06, RF-09, DT-24): listar, crear y desbloquear.

Vive en infraestructura, junto a `api/autenticacion.py`, porque el bloqueo y el hash de la
contraseña son datos de la cuenta que el dominio no modela. El permiso (solo administrador) lo
exige el decorador de la vista y el contrato.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction

from dominio.acceso import PoliticaBloqueo
from dominio.errores import CorreoDuplicado, UsuarioNoEncontrado
from dominio.modelos import Rol
from infraestructura.persistencia.models import UsuarioModelo

POLITICA = PoliticaBloqueo()


def listar() -> list[UsuarioModelo]:
    return list(UsuarioModelo.objects.order_by("nombre"))


def esta_bloqueada(cuenta: UsuarioModelo, ahora: datetime) -> bool:
    return POLITICA.esta_bloqueada(cuenta.bloqueada_hasta, ahora)


def _correo_en_uso(correo: str) -> bool:
    return UsuarioModelo.objects.filter(correo__iexact=correo.strip()).exists()


def crear(nombre: str, correo: str, rol: Rol, clave: str) -> UsuarioModelo:
    """La contraseña inicial la define el administrador y se guarda solo como hash."""
    if _correo_en_uso(correo):
        raise CorreoDuplicado(f"Ya hay una cuenta con el correo {correo}.")
    try:
        with transaction.atomic():
            return UsuarioModelo.objects.create(
                nombre=nombre.strip(),
                correo=correo.strip().lower(),
                rol=rol.value,
                clave_hash=make_password(clave),
            )
    except IntegrityError as error:  # dos administradores creando el mismo correo a la vez
        raise CorreoDuplicado(f"Ya hay una cuenta con el correo {correo}.") from error


def desbloquear(usuario_id: UUID) -> UsuarioModelo:
    cuenta = UsuarioModelo.objects.filter(id=usuario_id).first()
    if cuenta is None:
        raise UsuarioNoEncontrado(f"No existe la cuenta {usuario_id}.")
    cuenta.intentos_fallidos, cuenta.bloqueada_hasta = 0, None
    cuenta.save(update_fields=["intentos_fallidos", "bloqueada_hasta"])
    return cuenta
