"""Entidades y enumeraciones del dominio de FitManage (Python puro)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from dominio.errores import DatosInvalidos, MotivoRequerido, PagoNoAnulable


class TipoDocumento(Enum):
    CC = "CC"
    CE = "CE"
    PPT = "PPT"
    PASAPORTE = "PASAPORTE"


class Rol(Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    RECEPCIONISTA = "RECEPCIONISTA"
    ENTRENADOR = "ENTRENADOR"


class MedioPago(Enum):
    EFECTIVO = "EFECTIVO"
    NEQUI = "NEQUI"
    DAVIPLATA = "DAVIPLATA"
    TRANSFERENCIA = "TRANSFERENCIA"

    def requiere_referencia(self) -> bool:
        """RN-06: todo medio distinto de efectivo exige el número del comprobante."""
        return self is not MedioPago.EFECTIVO


class EstadoPago(Enum):
    VIGENTE = "VIGENTE"
    ANULADO = "ANULADO"


class EstadoMembresia(Enum):
    ACTIVO = "ACTIVO"
    VENCIDO = "VENCIDO"
    SIN_MEMBRESIA = "SIN_MEMBRESIA"


@dataclass(frozen=True)
class Socio:
    tipo_documento: TipoDocumento
    numero_documento: str
    nombres: str
    apellidos: str
    telefono: str
    autorizacion_datos: datetime | None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.numero_documento.strip():
            raise DatosInvalidos("El número de documento es obligatorio.")
        if self.autorizacion_datos is None:
            # RN-02 / Ley 1581 de 2012
            raise DatosInvalidos("El socio debe autorizar el tratamiento de sus datos.")


@dataclass
class Plan:
    nombre: str
    duracion_dias: int
    precio: Decimal
    activo: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.duracion_dias <= 0 or self.precio <= 0:
            raise DatosInvalidos("La duración y el precio deben ser mayores que cero.")

    def desactivar(self) -> None:
        """RN-09: un plan con pagos no se elimina, se desactiva."""
        self.activo = False


@dataclass(frozen=True)
class Usuario:
    nombre: str
    correo: str
    rol: Rol
    activo: bool = True
    id: UUID = field(default_factory=uuid4)

    def es_administrador(self) -> bool:
        return self.rol is Rol.ADMINISTRADOR and self.activo


@dataclass(frozen=True)
class SolicitudPago:
    """Datos que digita la recepcionista para registrar un pago (CU-01)."""

    tipo_documento: TipoDocumento
    numero_documento: str
    plan_id: UUID
    medio: str
    referencia: str | None = None


@dataclass
class Pago:
    socio: Socio
    plan_id: UUID
    valor: Decimal
    duracion_dias: int
    medio: MedioPago
    referencia: str | None
    fecha_inicio: date
    fecha_vencimiento: date
    registrado_por: Usuario
    registrado_en: datetime
    estado: EstadoPago = EstadoPago.VIGENTE
    fecha_anulacion: datetime | None = None
    anulado_por: Usuario | None = None
    motivo_anulacion: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.fecha_vencimiento < self.fecha_inicio:
            raise DatosInvalidos("El vencimiento no puede ser anterior al inicio.")

    def esta_vigente(self) -> bool:
        return self.estado is EstadoPago.VIGENTE and self.fecha_anulacion is None

    def anular(self, motivo: str, anulado_por: Usuario, ahora: datetime) -> None:
        """RN-07: la anulación es lógica, ocurre una sola vez y exige motivo."""
        if not self.esta_vigente():
            raise PagoNoAnulable("El pago ya está anulado.")
        if not motivo or not motivo.strip():
            raise MotivoRequerido("Indique el motivo de la anulación.")
        self.estado = EstadoPago.ANULADO
        self.fecha_anulacion = ahora
        self.anulado_por = anulado_por
        self.motivo_anulacion = motivo.strip()
