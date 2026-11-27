"""Salida de la IA, copiada sin cambios (fragmento relevante). NO se usa en el código de FitManage.

Prompt: «Refactoriza infraestructura/api/autenticacion.py de FitManage aplicando inversión de
dependencias: que no use UsuarioModelo directamente sino un puerto, con un doble en memoria
para las pruebas.»
"""

from __future__ import annotations

from typing import Protocol


class CuentaRepositorio(Protocol):
    def por_correo(self, correo: str) -> UsuarioModelo | None: ...  # noqa: F821

    def guardar(self, cuenta: UsuarioModelo) -> None: ...  # noqa: F821


class CuentasEnMemoria:
    def __init__(self, *cuentas) -> None:
        self._cuentas = {c.correo: c for c in cuentas}

    def por_correo(self, correo: str):
        return self._cuentas.get(correo)

    def guardar(self, cuenta) -> None:
        self._cuentas[cuenta.correo] = cuenta


# Y en iniciar_sesion:
#     cuenta = self._cuentas.por_correo(correo)        # reemplaza select_for_update().filter(...)
#     resultado = _verificar(cuenta, clave, ahora)
#     ...
#     self._cuentas.guardar(cuenta)
