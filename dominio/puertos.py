"""Puertos (interfaces) que el dominio necesita del exterior.

La infraestructura los implementa (Django ORM, reloj de Bogotá); las pruebas
usan dobles en memoria. El dominio nunca importa Django ni la base de datos.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from dominio.auditoria import EventoAuditoria
from dominio.errores import DatosInvalidos
from dominio.modelos import Pago, Plan, Socio, TipoDocumento, Usuario


class SocioRepositorio(Protocol):
    def buscar_por_documento(self, tipo: TipoDocumento, numero: str) -> Socio | None: ...

    def guardar(self, socio: Socio) -> None: ...

    def eliminar(self, socio: Socio) -> None: ...


class PlanRepositorio(Protocol):
    def obtener(self, plan_id: UUID) -> Plan | None: ...

    def guardar(self, plan: Plan) -> None: ...

    def todos(self) -> list[Plan]: ...


class PagoRepositorio(Protocol):
    def vigentes_de(self, socio: Socio) -> list[Pago]: ...

    def existe_referencia_vigente(self, referencia: str) -> bool: ...

    def tiene_pagos(self, socio: Socio) -> bool:
        """Vigentes o anulados: un pago anulado también es un registro contable."""
        ...

    def obtener(self, pago_id: UUID) -> Pago | None: ...

    def guardar(self, pago: Pago) -> None: ...


class UsuarioRepositorio(Protocol):
    """Puerto del contexto Acceso del personal: dueño de las cuentas (paga DT-11)."""

    def obtener(self, usuario_id: UUID) -> Usuario | None: ...

    def guardar(self, usuario: Usuario) -> None: ...


class CorreoSaliente(Protocol):
    """Frontera con el servidor de correo (SMTP del hosting, DAD 8.2).

    Precondición: `destinatario` es una dirección con «@»; si no, `DatosInvalidos` sin enviar.
    Poscondición: si `enviar` retorna, el servidor aceptó el mensaje para ese destinatario.
    Si no responde o no lo acepta, `CorreoNoDisponible`. Ninguna variante declara éxito sin
    entregar (Software III, Guía 09; lo prueba tests/integracion/test_contrato_correo.py).
    """

    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None: ...


class RegistroAuditoria(Protocol):
    """Guarda un evento en la misma transacción de la operación que lo produjo (ADR N.° 19)."""

    def registrar(self, evento: EventoAuditoria) -> None: ...


class SinAuditoria:
    """Para las pruebas del núcleo que no miran el rastro. La API siempre usa el adaptador real."""

    def registrar(self, evento: EventoAuditoria) -> None:
        return None


class Reloj(Protocol):
    """Entrega la fecha y hora en la zona America/Bogota (RN-03)."""

    def hoy(self) -> date: ...

    def ahora(self) -> datetime: ...


def exigir_destinatario(destinatario: str) -> str:
    """Precondición común de toda variante de `CorreoSaliente`."""
    limpio = destinatario.strip()
    if "@" not in limpio:
        raise DatosInvalidos("El correo del destinatario no es válido.")
    return limpio
