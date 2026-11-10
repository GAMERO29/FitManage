"""Casos de uso de pagos: CU-01 Registrar pago, RF-10 Anular pago y cambio de plan (SRP, FPI-11)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from dominio.calculadora import CalculadoraMembresia
from dominio.errores import (
    DatosInvalidos,
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


@dataclass(frozen=True)
class VistaPreviaPago:
    """Lo que quedaría si se registra el pago ahora: el cliente lo muestra, no lo calcula."""

    plan: Plan
    inicia: date
    vence: date


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
        fecha_inicio, fecha_vencimiento = self._periodo(socio, plan)
        pago = Pago(
            socio=socio,
            plan_id=plan.id,
            valor=plan.precio,  # RN-08: copia del precio vigente
            duracion_dias=plan.duracion_dias,
            medio=medio,
            referencia=referencia,
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=fecha_vencimiento,
            registrado_por=usuario,
            registrado_en=self._reloj.ahora(),
        )
        self._pagos.guardar(pago)
        return pago

    def periodo_desde(self, anterior: Pago, plan_id: UUID) -> VistaPreviaPago:
        """Cambio de plan: el plan nuevo empieza el mismo día que el pago que reemplaza."""
        plan = self._buscar_plan(plan_id)
        if plan.id == anterior.plan_id:
            raise DatosInvalidos("El socio ya tiene ese plan.")
        inicia = anterior.fecha_inicio
        return VistaPreviaPago(
            plan, inicia, self._calculadora.calcular_vencimiento(inicia, plan.duracion_dias)
        )

    def registrar_cambio(
        self, anterior: Pago, plan_id: UUID, medio: str, referencia: str | None, usuario: Usuario
    ) -> Pago:
        """Registra el pago del plan nuevo; el anterior ya está anulado (CambioPlanService)."""
        previa = self.periodo_desde(anterior, plan_id)
        medio_pago = self._convertir_medio(medio)
        pago = Pago(
            socio=anterior.socio,
            plan_id=previa.plan.id,
            valor=previa.plan.precio,  # RN-08 y A3: el precio completo del plan nuevo
            duracion_dias=previa.plan.duracion_dias,
            medio=medio_pago,
            referencia=self._validar_referencia(medio_pago, referencia),
            fecha_inicio=previa.inicia,
            fecha_vencimiento=previa.vence,
            registrado_por=usuario,
            registrado_en=self._reloj.ahora(),
        )
        self._pagos.guardar(pago)
        return pago

    def vista_previa(self, tipo: TipoDocumento, numero: str, plan_id: UUID) -> VistaPreviaPago:
        """Las mismas reglas del registro (RN-03, RN-04, RN-08), sin guardar nada."""
        socio = self._buscar_socio(tipo, numero)
        plan = self._buscar_plan(plan_id)
        inicia, vence = self._periodo(socio, plan)
        return VistaPreviaPago(plan, inicia, vence)

    def _periodo(self, socio: Socio, plan: Plan) -> tuple[date, date]:
        inicia = self._calculadora.calcular_fecha_inicio(
            self._pagos.vigentes_de(socio), self._reloj.hoy()
        )
        return inicia, self._calculadora.calcular_vencimiento(inicia, plan.duracion_dias)

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
        # Aviso rápido y claro; la garantía la da el índice único de la base (DT-01).
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
        return self._anular(self.verificar_anulable(pago_id, usuario), usuario, motivo)

    def verificar_anulable(self, pago_id: UUID, usuario: Usuario) -> Pago:
        """Las mismas condiciones de la anulación, sin cambiar nada (sirve para la vista previa)."""
        self._exigir_administrador(usuario)
        pago = self._pagos.obtener(pago_id)
        if pago is None:
            raise PagoNoEncontrado(f"No existe el pago {pago_id}.")
        if not pago.esta_vigente():
            raise PagoNoAnulable("El pago ya está anulado.")
        ultimo = self._ultimo_vigente(pago.socio)
        if ultimo is None or ultimo.id != pago.id:
            raise PagoNoAnulable("Solo se puede anular el último pago vigente del socio.")
        return pago

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


@dataclass(frozen=True)
class CambioDePlan:
    anulado: Pago
    nuevo: Pago
    diferencia: int  # lo que el socio paga de más (positivo) o se le devuelve (negativo)


class CambioPlanService:
    """Cambia el plan de un socio: anula su último pago y registra el nuevo desde el mismo día.

    Es la secuencia que ya hacía el administrador a mano (CU-03 seguido de CU-01), en un solo paso.
    La vista la ejecuta dentro de una transacción: si el pago nuevo no se puede registrar, la
    anulación tampoco queda.
    """

    def __init__(self, anulacion: AnulacionPagoService, registro: RegistroPagoService) -> None:
        self._anulacion = anulacion
        self._registro = registro

    def vista_previa(
        self, pago_id: UUID, plan_id: UUID, usuario: Usuario
    ) -> tuple[Pago, VistaPreviaPago]:
        anterior = self._anulacion.verificar_anulable(pago_id, usuario)
        return anterior, self._registro.periodo_desde(anterior, plan_id)

    def cambiar(
        self,
        pago_id: UUID,
        plan_id: UUID,
        medio: str,
        referencia: str | None,
        motivo: str,
        usuario: Usuario,
    ) -> CambioDePlan:
        anterior, _ = self.vista_previa(pago_id, plan_id, usuario)  # valida antes de tocar nada
        anulado = self._anulacion.anular(anterior.id, usuario, motivo)
        nuevo = self._registro.registrar_cambio(anulado, plan_id, medio, referencia, usuario)
        return CambioDePlan(anulado, nuevo, int(nuevo.valor - anulado.valor))
