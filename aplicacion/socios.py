"""Casos de uso de socios: CU-02 Registrar socio y CU-03 Consultar estado (paga DT-16, Guía 15).

Hasta la Guía 14 vivían dentro de los controladores HTTP: creaban la entidad, usaban los
repositorios de Django y llamaban a la calculadora. Ahora el controlador solo traduce HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from dominio.calculadora import CalculadoraMembresia
from dominio.errores import SocioNoEncontrado
from dominio.modelos import EstadoMembresia, Socio, TipoDocumento
from dominio.puertos import PagoRepositorio, Reloj, SocioRepositorio


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
