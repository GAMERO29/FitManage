"""Casos de uso de pagos: CU-01 Registrar pago y RF-10 Anular pago (SRP, FPI-11)."""

from __future__ import annotations

from uuid import UUID

from dominio.calculadora import CalculadoraMembresia
from dominio.errores import (
    MedioPagoInvalido,
    PagoNoAnulable,
    PagoNoEncontrado,
    PermisoDenegado,
    PlanNoDisponible,
    ReferenciaDuplicada,
    ReferenciaRequerida,
    SocioNoEncontrado,
)
from dominio.modelos import (
    MedioPago,
    Pago,
    Plan,
    Socio,
    SolicitudPago,
    TipoDocumento,
    Usuario,
)
from dominio.puertos import PagoRepositorio, PlanRepositorio, Reloj, SocioRepositorio


class RegistroPagoService:
    """CU-01 Registrar pago de membresía."""

    def __init__(
        self,
        socios: SocioRepositorio,
        planes: PlanRepositorio,
        pagos: PagoRepositorio,
        reloj: Reloj,
        calculadora: CalculadoraMembresia | None = None,
    ) -> None:
        self._socios = socios
        self._planes = planes
        self._pagos = pagos
        self._reloj = reloj
        self._calculadora = calculadora or CalculadoraMembresia()

    def registrar_pago(self, solicitud: SolicitudPago, usuario: Usuario) -> Pago:
        socio = self._buscar_socio(solicitud.tipo_documento, solicitud.numero_documento)
        plan = self._buscar_plan(solicitud.plan_id)
        medio = self._convertir_medio(solicitud.medio)
        referencia = self._validar_referencia(medio, solicitud.referencia)

        fecha_inicio = self._calculadora.calcular_fecha_inicio(
            self._pagos.vigentes_de(socio), self._reloj.hoy()
        )
        pago = Pago(
            socio=socio,
            plan_id=plan.id,
            valor=plan.precio,  # RN-08: copia del precio vigente
            duracion_dias=plan.duracion_dias,
            medio=medio,
            referencia=referencia,
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=self._calculadora.calcular_vencimiento(
                fecha_inicio, plan.duracion_dias
            ),
            registrado_por=usuario,
            registrado_en=self._reloj.ahora(),
        )
        self._pagos.guardar(pago)
        return pago

    def _buscar_socio(self, tipo: TipoDocumento, numero: str) -> Socio:
        socio = self._socios.buscar_por_documento(tipo, numero.strip())
        if socio is None:
            raise SocioNoEncontrado(f"No hay socio con documento {tipo.value} {numero}.")
        return socio

    def _buscar_plan(self, plan_id: UUID) -> Plan:
        plan = self._planes.obtener(plan_id)
        if plan is None or not plan.activo:
            raise PlanNoDisponible("El plan no existe o está desactivado.")
        return plan

    @staticmethod
    def _convertir_medio(medio: str) -> MedioPago:
        try:
            return MedioPago(medio.strip().upper())
        except ValueError as error:
            raise MedioPagoInvalido(f"Medio de pago no aceptado: {medio}.") from error

    def _validar_referencia(self, medio: MedioPago, referencia: str | None) -> str | None:
        if not medio.requiere_referencia():
            return None
        referencia = (referencia or "").strip()
        if not referencia:
            raise ReferenciaRequerida(f"Para pagos por {medio.value} digite el comprobante.")
        # DT-01: la verificación y el guardado no son atómicos (ver inventario de deuda).
        if self._pagos.existe_referencia_vigente(referencia):
            raise ReferenciaDuplicada(f"La referencia {referencia} ya está en un pago vigente.")
        return referencia


class AnulacionPagoService:
    """RF-10 / CU-03 Anular el último pago vigente de un socio."""

    def __init__(self, pagos: PagoRepositorio, reloj: Reloj) -> None:
        self._pagos = pagos
        self._reloj = reloj

    def anular_ultimo(self, socio: Socio, usuario: Usuario, motivo: str) -> Pago:
        self._exigir_administrador(usuario)
        ultimo = self._ultimo_vigente(socio)
        if ultimo is None:
            raise PagoNoAnulable("El socio no tiene pagos vigentes.")
        return self._anular(ultimo, usuario, motivo)

    def anular(self, pago_id: UUID, usuario: Usuario, motivo: str) -> Pago:
        """`PATCH /pagos/{pagoId}`: solo se acepta si ese pago es el último vigente de su socio."""
        self._exigir_administrador(usuario)
        pago = self._pagos.obtener(pago_id)
        if pago is None:
            raise PagoNoEncontrado(f"No existe el pago {pago_id}.")
        if not pago.esta_vigente():
            raise PagoNoAnulable("El pago ya está anulado.")
        ultimo = self._ultimo_vigente(pago.socio)
        if ultimo is None or ultimo.id != pago.id:
            raise PagoNoAnulable("Solo se puede anular el último pago vigente del socio.")
        return self._anular(pago, usuario, motivo)

    @staticmethod
    def _exigir_administrador(usuario: Usuario) -> None:
        if not usuario.es_administrador():
            raise PermisoDenegado("Solo un administrador puede anular pagos.")

    def _ultimo_vigente(self, socio: Socio) -> Pago | None:
        vigentes = self._pagos.vigentes_de(socio)
        return max(vigentes, key=lambda p: (p.fecha_inicio, p.registrado_en), default=None)

    def _anular(self, pago: Pago, usuario: Usuario, motivo: str) -> Pago:
        pago.anular(motivo, usuario, self._reloj.ahora())
        self._pagos.guardar(pago)
        return pago
