"""Puertos (interfaces) que el dominio necesita del exterior.

La infraestructura los implementa (Django ORM, reloj de Bogotá); las pruebas
usan dobles en memoria. El dominio nunca importa Django ni la base de datos.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from dominio.modelos import Pago, Plan, Socio, TipoDocumento, Usuario


class SocioRepositorio(Protocol):
    def buscar_por_documento(self, tipo: TipoDocumento, numero: str) -> Socio | None: ...

    def guardar(self, socio: Socio) -> None: ...


class PlanRepositorio(Protocol):
    def obtener(self, plan_id: UUID) -> Plan | None: ...


class PagoRepositorio(Protocol):
    def vigentes_de(self, socio: Socio) -> list[Pago]: ...

    def existe_referencia_vigente(self, referencia: str) -> bool: ...

    def obtener(self, pago_id: UUID) -> Pago | None: ...

    def guardar(self, pago: Pago) -> None: ...


class UsuarioRepositorio(Protocol):
    """Puerto del contexto Acceso del personal: dueño de las cuentas (paga DT-11)."""

    def obtener(self, usuario_id: UUID) -> Usuario | None: ...

    def guardar(self, usuario: Usuario) -> None: ...


class CorreoSaliente(Protocol):
    """Frontera con el servidor de correo (SMTP del hosting, DAD 8.2).

    Lanza `CorreoNoDisponible` si el servidor no acepta el mensaje.
    """

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None: ...


class Reloj(Protocol):
    """Entrega la fecha y hora en la zona America/Bogota (RN-03)."""

    def hoy(self) -> date: ...

    def ahora(self) -> datetime: ...
