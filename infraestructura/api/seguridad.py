"""Decorador de cada vista: JWT (o la excepción declarada), rol y contrato, en ese orden."""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps
from uuid import UUID

from django.db import InterfaceError, OperationalError
from django.http import HttpRequest, JsonResponse

from dominio.errores import ErrorDeDominio
from dominio.modelos import Rol, Usuario
from infraestructura.api import contrato, tokens
from infraestructura.api.errores import respuesta_de_error
from infraestructura.api.http import SolicitudInvalida, no_autenticado, problema
from infraestructura.persistencia.repositorios import UsuarioRepositorioORM

TODO_EL_PERSONAL = (Rol.RECEPCIONISTA, Rol.ADMINISTRADOR)
SOLO_ADMINISTRADOR = (Rol.ADMINISTRADOR,)
registro = logging.getLogger("fitmanage.api")


def _usuario_del_token(request: HttpRequest) -> Usuario | None:
    encabezado = request.headers.get("Authorization", "")
    esquema, _, token = encabezado.partition(" ")
    if esquema.lower() != "bearer" or not token:
        return None
    try:
        claims = tokens.leer_acceso(token)
        usuario = UsuarioRepositorioORM().obtener(UUID(claims["sub"]))
    except (tokens.TokenInvalido, ValueError):
        return None
    return usuario if usuario and usuario.activo else None


def _solicitud_invalida(errores: list[dict]) -> JsonResponse:
    return problema(400, "SOLICITUD_INVALIDA", "Solicitud inválida", errores=errores)


def endpoint(roles: tuple[Rol, ...] | None) -> Callable:
    """`roles=None` solo para los endpoints que el contrato declara con otra seguridad."""

    def decorador(vista: Callable) -> Callable:
        @wraps(vista)
        def envoltura(request: HttpRequest, *args, **kwargs) -> JsonResponse:
            # Software III, Guías 02 y 06: si la base no responde, es una falla técnica y no un
            # error de negocio; el consumidor recibe 503 en problem+json, no la página HTML del 500.
            try:
                return _atender(request, *args, **kwargs)
            except (OperationalError, InterfaceError):
                registro.warning("base de datos no disponible", extra={"evento": "base_caida"})
                return problema(
                    503,
                    "SERVICIO_NO_DISPONIBLE",
                    "Servicio no disponible",
                    detalle="La base de datos no responde. Intente de nuevo en un minuto.",
                    encabezados={"Retry-After": "60"},
                )

        def _atender(request: HttpRequest, *args, **kwargs) -> JsonResponse:
            if roles is not None:
                usuario = _usuario_del_token(request)
                if usuario is None:
                    return no_autenticado()
                if usuario.rol not in roles:
                    return problema(403, "SIN_PERMISO", "Su rol no puede hacer esto")
                request.usuario = usuario
            falta_credencial, errores = contrato.revisar(request)
            if falta_credencial:
                return no_autenticado()
            if errores:
                return _solicitud_invalida(errores)
            try:
                return vista(request, *args, **kwargs)
            except SolicitudInvalida as error:
                return _solicitud_invalida(error.errores)
            except ErrorDeDominio as error:
                return respuesta_de_error(error)

        return envoltura

    return decorador
