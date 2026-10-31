"""Casos de uso del contexto Acceso del personal."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from dominio.errores import PermisoDenegado, UsuarioNoEncontrado
from dominio.modelos import Usuario
from dominio.puertos import CorreoSaliente, UsuarioRepositorio

VIGENCIA_ENLACE_MINUTOS = 30


class RestablecimientoClaveService:
    """UC-06: el administrador envía a una cuenta un enlace para crear contraseña nueva.

    El correo es la única dependencia externa de la API; si falla, `CorreoNoDisponible`
    sube sin que nada haya cambiado (el enlace es firmado y no se guarda).
    """

    def __init__(
        self,
        usuarios: UsuarioRepositorio,
        correo: CorreoSaliente,
        enlace_para: Callable[[Usuario], str],
    ) -> None:
        self._usuarios = usuarios
        self._correo = correo
        self._enlace_para = enlace_para

    def restablecer(self, usuario_id: UUID, solicitante: Usuario) -> Usuario:
        if not solicitante.es_administrador():
            raise PermisoDenegado("Solo un administrador puede restablecer contraseñas.")
        usuario = self._usuarios.obtener(usuario_id)
        if usuario is None:
            raise UsuarioNoEncontrado(f"No existe la cuenta {usuario_id}.")
        self._correo.enviar(
            usuario.correo,
            "FitManage: crea tu contraseña nueva",
            f"Hola {usuario.nombre}:\n\n"
            f"{solicitante.nombre} pidió restablecer tu contraseña. Entra a este enlace "
            f"para crear una nueva; vence en {VIGENCIA_ENLACE_MINUTOS} minutos:\n\n"
            f"{self._enlace_para(usuario)}\n\n"
            "Si no lo esperabas, avísale al administrador del gimnasio.",
        )
        return usuario
