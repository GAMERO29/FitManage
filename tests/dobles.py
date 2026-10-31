"""Dobles de prueba: repositorios en memoria y un reloj fijo (LSP: mismo contrato)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from dominio.modelos import Pago, Plan, Socio, TipoDocumento, Usuario


class SociosEnMemoria:
    def __init__(self, *socios: Socio) -> None:
        self._socios = {(s.tipo_documento, s.numero_documento): s for s in socios}

    def buscar_por_documento(self, tipo: TipoDocumento, numero: str) -> Socio | None:
        return self._socios.get((tipo, numero))

    def guardar(self, socio: Socio) -> None:
        self._socios[(socio.tipo_documento, socio.numero_documento)] = socio


class PlanesEnMemoria:
    def __init__(self, *planes: Plan) -> None:
        self._planes = {p.id: p for p in planes}

    def obtener(self, plan_id: UUID) -> Plan | None:
        return self._planes.get(plan_id)


class PagosEnMemoria:
    def __init__(self, *pagos: Pago) -> None:
        self._pagos: dict[UUID, Pago] = {p.id: p for p in pagos}

    def vigentes_de(self, socio: Socio) -> list[Pago]:
        return [p for p in self._pagos.values() if p.socio.id == socio.id and p.esta_vigente()]

    def existe_referencia_vigente(self, referencia: str) -> bool:
        return any(p.referencia == referencia and p.esta_vigente() for p in self._pagos.values())

    def guardar(self, pago: Pago) -> None:
        self._pagos[pago.id] = pago

    def todos(self) -> list[Pago]:
        return list(self._pagos.values())


class RelojFijo:
    def __init__(self, ahora: datetime) -> None:
        self._ahora = ahora

    def hoy(self) -> date:
        return self._ahora.date()

    def ahora(self) -> datetime:
        return self._ahora


class UsuariosEnMemoria:
    def __init__(self, *usuarios: Usuario) -> None:
        self._usuarios = {u.id: u for u in usuarios}

    def obtener(self, usuario_id: UUID) -> Usuario | None:
        return self._usuarios.get(usuario_id)

    def guardar(self, usuario: Usuario) -> None:
        self._usuarios[usuario.id] = usuario
