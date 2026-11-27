"""Casos de uso de socios: CU-02 Registrar socio y CU-03 Consultar estado (paga DT-16, Guía 15).

Hasta la Guía 14 vivían dentro de los controladores HTTP: creaban la entidad, usaban los
repositorios de Django y llamaban a la calculadora. Ahora el controlador solo traduce HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from dominio.auditoria import EventoAuditoria, TipoEvento
from dominio.calculadora import CalculadoraMembresia
from dominio.errores import PermisoDenegado, SocioConPagos, SocioNoEncontrado
from dominio.modelos import EstadoMembresia, Socio, TipoDocumento, Usuario
from dominio.puertos import (
    PagoRepositorio,
    RegistroAuditoria,
    Reloj,
    SinAuditoria,
    SocioRepositorio,
)


class RegistroSocioService:
    """CU-02: la autorización de datos (Ley 1581) queda con la hora del registro."""

    def __init__(self, socios: SocioRepositorio, reloj: Reloj) -> None:
        self._socios = socios
        self._reloj = reloj

    def registrar(
        self, tipo: TipoDocumento, numero: str, nombres: str, apellidos: str, telefono: str
    ) -> Socio:
        socio = Socio(
            tipo_documento=tipo,
            numero_documento=numero,
            nombres=nombres.strip(),
            apellidos=apellidos.strip(),
            telefono=telefono,
            autorizacion_datos=self._reloj.ahora(),
        )
        self._socios.guardar(socio)  # DocumentoDuplicado si el documento ya existe
        return socio


@dataclass(frozen=True)
class EstadoSocio:
    socio: Socio
    estado: EstadoMembresia
    vence: date | None
    hoy: date


class ConsultaEstadoService:
    """CU-03: el estado no se guarda; se deriva de los pagos vigentes (RN-05)."""

    def __init__(
        self,
        socios: SocioRepositorio,
        pagos: PagoRepositorio,
        reloj: Reloj,
        calculadora: CalculadoraMembresia | None = None,
    ) -> None:
        self._socios = socios
        self._pagos = pagos
        self._reloj = reloj
        self._calculadora = calculadora or CalculadoraMembresia()

    def consultar(self, tipo: TipoDocumento, numero: str) -> EstadoSocio:
        socio = self._socios.buscar_por_documento(tipo, numero)
        if socio is None:
            raise SocioNoEncontrado("No hay ningún socio con ese documento")
        hoy = self._reloj.hoy()
        estado, vence = self._calculadora.estado_de(self._pagos.vigentes_de(socio), hoy)
        return EstadoSocio(socio, estado, vence, hoy)


class SupresionSocioService:
    """Software III, Guía 06: suprime los datos de un socio sin pagos (Ley 1581, supresión).

    Contrato: entrada (tipo, número, solicitante); salida: nada si se suprimió.
    Errores de negocio: `PermisoDenegado` (no es administrador), `SocioNoEncontrado` y
    `SocioConPagos` (los pagos son registros contables y no se borran). Un fallo de la base no es un
    error de negocio: sube tal cual y el adaptador HTTP lo traduce a 503.
    """

    def __init__(
        self,
        socios: SocioRepositorio,
        pagos: PagoRepositorio,
        reloj: Reloj,
        auditoria: RegistroAuditoria | None = None,
    ) -> None:
        self._socios = socios
        self._pagos = pagos
        self._reloj = reloj
        self._auditoria = auditoria or SinAuditoria()

    def suprimir(self, tipo: TipoDocumento, numero: str, solicitante: Usuario) -> None:
        if not solicitante.es_administrador():
            raise PermisoDenegado("Solo el administrador suprime los datos de un socio.")
        socio = self._socios.buscar_por_documento(tipo, numero)
        if socio is None:
            raise SocioNoEncontrado("No hay ningún socio con ese documento")
        if self._pagos.tiene_pagos(socio):
            raise SocioConPagos(
                "El socio tiene pagos. Los pagos son registros contables y se conservan."
            )
        self._socios.eliminar(socio)
        # El evento no guarda el nombre ni el documento: justamente se están suprimiendo.
        self._auditoria.registrar(
            EventoAuditoria(
                TipoEvento.SOCIO_SUPRIMIDO, solicitante, self._reloj.ahora(), socio.id, None, {}
            )
        )
