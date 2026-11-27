"""Casos de uso de pagos: CU-01 Registrar pago, RF-10 Anular pago y cambio de plan (SRP, FPI-11)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from dominio.auditoria import EventoAuditoria, TipoEvento, datos_del_pago
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
from dominio.historial import HistorialPagos
from dominio.modelos import (
    MedioPago,
    Pago,
    Plan,
    Rol,
    Socio,
    SolicitudPago,
    TipoDocumento,
    Usuario,
)
from dominio.politicas import PoliticaAnulacion, RecepcionistaCorrigeSuDia
from dominio.puertos import (
    PagoRepositorio,
    PlanRepositorio,
    RegistroAuditoria,
    Reloj,
    SinAuditoria,
    SocioRepositorio,
)


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
        auditoria: RegistroAuditoria | None = None,
    ) -> None:
        self._socios = socios
        self._planes = planes
        self._pagos = pagos
        self._reloj = reloj
        self._calculadora = calculadora or CalculadoraMembresia()
        self._auditoria = auditoria or SinAuditoria()

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
        self._auditoria.registrar(
            EventoAuditoria(
                TipoEvento.PAGO_REGISTRADO,
                usuario,
                pago.registrado_en,
                pago.id,
                socio.id,
                {**datos_del_pago(pago), "plan": plan.nombre},
            )
        )
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

    def nombre_del_plan(self, plan_id: UUID) -> str:
        return self._buscar_plan(plan_id).nombre

    def vista_previa(self, tipo: TipoDocumento, numero: str, plan_id: UUID) -> VistaPreviaPago:
        """Las mismas reglas del registro (RN-03, RN-04, RN-08), sin guardar nada."""
        socio = self._buscar_socio(tipo, numero)
        plan = self._buscar_plan(plan_id)
        inicia, vence = self._periodo(socio, plan)
        return VistaPreviaPago(plan, inicia, vence)

    def _periodo(self, socio: Socio, plan: Plan) -> tuple[date, date]:
        historial = HistorialPagos(socio, self._pagos.vigentes_de(socio))
        periodo = historial.periodo_del_siguiente(self._reloj.hoy(), plan.duracion_dias)
        return periodo.inicia, periodo.vence

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
    """RF-10 / CU-03 Anular el último pago vigente de un socio (ADR N.° 18).

    El administrador anula cualquier último pago vigente. La recepcionista solo anula los pagos
    que ella misma registró hoy, para corregir un error en el momento: así no puede cobrar en
    efectivo un día y anular el pago después. Para cambiar el plan del socio no tiene ese límite.
    Quién puede anular lo decide la `PoliticaAnulacion` que se inyecta (Software III, Guía 03).
    """

    def __init__(
        self,
        pagos: PagoRepositorio,
        reloj: Reloj,
        auditoria: RegistroAuditoria | None = None,
        politica: PoliticaAnulacion | None = None,
    ) -> None:
        self._pagos = pagos
        self._reloj = reloj
        self._auditoria = auditoria or SinAuditoria()
        self._politica = politica or RecepcionistaCorrigeSuDia()

    def anular_ultimo(self, socio: Socio, usuario: Usuario, motivo: str) -> Pago:
        self._exigir_personal(usuario)
        ultimo = self._ultimo_vigente(socio)
        if ultimo is None:
            raise PagoNoAnulable("El socio no tiene pagos vigentes.")
        self._exigir_permiso(ultimo, usuario)
        return self._anular(ultimo, usuario, motivo)

    def anular(
        self, pago_id: UUID, usuario: Usuario, motivo: str, para_cambio_de_plan: bool = False
    ) -> Pago:
        """`PATCH /pagos/{pagoId}`: solo se acepta si ese pago es el último vigente de su socio."""
        pago = self.verificar_anulable(pago_id, usuario, para_cambio_de_plan)
        return self._anular(pago, usuario, motivo, registrar_evento=not para_cambio_de_plan)

    def verificar_anulable(
        self, pago_id: UUID, usuario: Usuario, para_cambio_de_plan: bool = False
    ) -> Pago:
        """Las mismas condiciones de la anulación, sin cambiar nada (sirve para la vista previa)."""
        self._exigir_personal(usuario)
        pago = self._pagos.obtener(pago_id)
        if pago is None:
            raise PagoNoEncontrado(f"No existe el pago {pago_id}.")
        HistorialPagos(pago.socio, self._pagos.vigentes_de(pago.socio)).exigir_que_sea_el_ultimo(
            pago
        )
        if not para_cambio_de_plan:
            self._exigir_permiso(pago, usuario)
        return pago

    def anulable_para(self, socio: Socio, pagos: list[Pago], usuario: Usuario) -> UUID | None:
        """El id del pago que `usuario` puede anular hoy en este historial, o None.

        Mismas reglas que `anular`, sin cambiar nada; el historial lo manda a la pantalla para que
        no repita la regla (Software III, Guía 13).
        """
        ultimo = HistorialPagos(socio, pagos).ultimo_vigente()
        if ultimo is None:
            return None
        try:
            self._exigir_personal(usuario)
            self._exigir_permiso(ultimo, usuario)
        except PermisoDenegado:
            return None
        return ultimo.id

    @staticmethod
    def _exigir_personal(usuario: Usuario) -> None:
        if not usuario.activo or usuario.rol not in (Rol.ADMINISTRADOR, Rol.RECEPCIONISTA):
            raise PermisoDenegado("Su rol no puede anular pagos ni cambiar planes.")

    def _exigir_permiso(self, pago: Pago, usuario: Usuario) -> None:
        self._politica.exigir(pago, usuario, self._reloj.hoy())

    def _ultimo_vigente(self, socio: Socio) -> Pago | None:
        return HistorialPagos(socio, self._pagos.vigentes_de(socio)).ultimo_vigente()

    def _anular(
        self, pago: Pago, usuario: Usuario, motivo: str, registrar_evento: bool = True
    ) -> Pago:
        pago.anular(motivo, usuario, self._reloj.ahora())
        self._pagos.guardar(pago)
        if registrar_evento:  # el cambio de plan deja un solo evento, PLAN_CAMBIADO
            self._auditoria.registrar(
                EventoAuditoria(
                    TipoEvento.PAGO_ANULADO,
                    usuario,
                    pago.fecha_anulacion,
                    pago.id,
                    pago.socio.id,
                    {**datos_del_pago(pago), "motivo": pago.motivo_anulacion},
                )
            )
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

    def __init__(
        self,
        anulacion: AnulacionPagoService,
        registro: RegistroPagoService,
        auditoria: RegistroAuditoria | None = None,
    ) -> None:
        self._anulacion = anulacion
        self._registro = registro
        self._auditoria = auditoria or SinAuditoria()

    def vista_previa(
        self, pago_id: UUID, plan_id: UUID, usuario: Usuario
    ) -> tuple[Pago, VistaPreviaPago]:
        anterior = self._anulacion.verificar_anulable(pago_id, usuario, para_cambio_de_plan=True)
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
        anulado = self._anulacion.anular(anterior.id, usuario, motivo, para_cambio_de_plan=True)
        nuevo = self._registro.registrar_cambio(anulado, plan_id, medio, referencia, usuario)
        cambio = CambioDePlan(anulado, nuevo, int(nuevo.valor - anulado.valor))
        self._auditoria.registrar(
            EventoAuditoria(
                TipoEvento.PLAN_CAMBIADO,
                usuario,
                nuevo.registrado_en,
                nuevo.id,
                nuevo.socio.id,
                {
                    "pagoAnulado": str(anulado.id),
                    "planAnteriorId": str(anulado.plan_id),
                    "valorAnterior": int(anulado.valor),
                    "registroDelAnulado": anulado.registrado_por.nombre,
                    "planNuevo": self._registro.nombre_del_plan(plan_id),
                    "valorNuevo": int(nuevo.valor),
                    "diferencia": cambio.diferencia,
                    "medio": nuevo.medio.value,
                    "motivo": anulado.motivo_anulacion,
                },
            )
        )
        return cambio
