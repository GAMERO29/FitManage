"""JWT de acceso y token de renovación (ADR N.° 06)."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from django.conf import settings

from dominio.modelos import Usuario

EMISOR = "fitmanage"
AUDIENCIA = "fitmanage-api"
VIGENCIA_ACCESO = timedelta(minutes=15)
VIGENCIA_RENOVACION = timedelta(hours=8)
ALGORITMO = "HS256"


class TokenInvalido(Exception):
    """Falta el token, venció, la firma no coincide o los claims no son los esperados."""


def ahora_real() -> datetime:
    """Los tokens viven en la hora real del servidor; el reloj del negocio es solo para fechas."""
    return datetime.now(UTC)


def emitir_acceso(usuario: Usuario) -> str:
    ahora = ahora_real()
    claims = {
        "sub": str(usuario.id),
        "rol": usuario.rol.value,
        "iss": EMISOR,
        "aud": AUDIENCIA,
        "iat": int(ahora.timestamp()),
        "exp": int((ahora + VIGENCIA_ACCESO).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(
        claims, settings.JWT_CLAVE, algorithm=ALGORITMO, headers={"kid": settings.JWT_KID}
    )


def leer_acceso(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_CLAVE,
            algorithms=[ALGORITMO],  # nunca "none" ni otro algoritmo que elija el cliente
            audience=AUDIENCIA,
            issuer=EMISOR,
            leeway=30,
            options={"require": ["exp", "iat", "sub", "jti"]},
        )
    except jwt.PyJWTError as error:
        raise TokenInvalido(str(error)) from error


def nuevo_token_renovacion() -> tuple[str, str]:
    """Devuelve (token para la cookie, huella SHA-256 que se guarda en la base)."""
    token = secrets.token_urlsafe(32)
    return token, huella(token)


def huella(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
