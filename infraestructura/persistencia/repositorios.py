"""Adaptadores de los puertos SocioRepositorio, PlanRepositorio y PagoRepositorio (paga DT-02)."""

from __future__ import annotations

from uuid import UUID

from django.db import IntegrityError, transaction

from dominio.errores import ReferenciaDuplicada
from dominio.modelos import (
    ZONA_HORARIA,
    EstadoPago,
    MedioPago,
    Pago,
    Plan,
    Rol,
    Socio,
    TipoDocumento,
    Usuario,
)
from infraestructura.persistencia.models import PagoModelo, PlanModelo, SocioModelo, UsuarioModelo

RESTRICCION_REFERENCIA = "referencia_vigente_unica"


def _a_socio(m: SocioModelo) -> Socio:
    return Socio(
        tipo_documento=TipoDocumento(m.tipo_documento),
        numero_documento=m.numero_documento,
        nombres=m.nombres,
        apellidos=m.apellidos,
        telefono=m.telefono,
        autorizacion_datos=m.autorizacion_datos.astimezone(ZONA_HORARIA),
        id=m.id,
    )


def _a_usuario(m: UsuarioModelo) -> Usuario:
    return Usuario(nombre=m.nombre, correo=m.correo, rol=Rol(m.rol), activo=m.activo, id=m.id)


def _a_pago(m: PagoModelo) -> Pago:
    return Pago(
        socio=_a_socio(m.socio),
        plan_id=m.plan_id,
        valor=m.valor,
        duracion_dias=m.duracion_dias,
        medio=MedioPago(m.medio),
        referencia=m.referencia,
        fecha_inicio=m.fecha_inicio,
        fecha_vencimiento=m.fecha_vencimiento,
        registrado_por=_a_usuario(m.registrado_por),
        registrado_en=m.registrado_en.astimezone(ZONA_HORARIA),
        estado=EstadoPago(m.estado),
        fecha_anulacion=m.fecha_anulacion.astimezone(ZONA_HORARIA) if m.fecha_anulacion else None,
        anulado_por=_a_usuario(m.anulado_por) if m.anulado_por else None,
        motivo_anulacion=m.motivo_anulacion,
        id=m.id,
    )


class UsuarioRepositorioORM:
    """Contexto Acceso del personal: es el único que escribe en la tabla usuarios (paga DT-11)."""

    def obtener(self, usuario_id: UUID) -> Usuario | None:
        m = UsuarioModelo.objects.filter(id=usuario_id).first()
        return _a_usuario(m) if m else None

    def guardar(self, usuario: Usuario) -> None:
        UsuarioModelo.objects.update_or_create(
            id=usuario.id,
            defaults={
                "nombre": usuario.nombre,
                "correo": usuario.correo,
                "rol": usuario.rol.value,
                "activo": usuario.activo,
            },
        )


class SocioRepositorioORM:
    def buscar_por_documento(self, tipo: TipoDocumento, numero: str) -> Socio | None:
        m = SocioModelo.objects.filter(tipo_documento=tipo.value, numero_documento=numero).first()
        return _a_socio(m) if m else None

    def guardar(self, socio: Socio) -> None:
        SocioModelo.objects.update_or_create(
            id=socio.id,
            defaults={
                "tipo_documento": socio.tipo_documento.value,
                "numero_documento": socio.numero_documento,
                "nombres": socio.nombres,
                "apellidos": socio.apellidos,
                "telefono": socio.telefono,
                "autorizacion_datos": socio.autorizacion_datos,
            },
        )


class PlanRepositorioORM:
    def obtener(self, plan_id: UUID) -> Plan | None:
        m = PlanModelo.objects.filter(id=plan_id).first()
        if m is None:
            return None
        return Plan(m.nombre, m.duracion_dias, m.precio, m.activo, id=m.id)

    def guardar(self, plan: Plan) -> None:
        PlanModelo.objects.update_or_create(
            id=plan.id,
            defaults={
                "nombre": plan.nombre,
                "duracion_dias": plan.duracion_dias,
                "precio": plan.precio,
                "activo": plan.activo,
            },
        )


class PagoRepositorioORM:
    def vigentes_de(self, socio: Socio) -> list[Pago]:
        consulta = PagoModelo.objects.select_related(
            "socio", "registrado_por", "anulado_por"
        ).filter(socio_id=socio.id, estado=EstadoPago.VIGENTE.value)
        return [_a_pago(m) for m in consulta]

    def existe_referencia_vigente(self, referencia: str) -> bool:
        return PagoModelo.objects.filter(
            referencia=referencia, estado=EstadoPago.VIGENTE.value
        ).exists()

    def guardar(self, pago: Pago) -> None:
        try:
            with transaction.atomic():
                PagoModelo.objects.update_or_create(id=pago.id, defaults=self._campos(pago))
        except IntegrityError as error:
            if RESTRICCION_REFERENCIA in str(error) or "pagos.referencia" in str(error):
                raise ReferenciaDuplicada(
                    f"La referencia {pago.referencia} ya está en un pago vigente."
                ) from error
            raise

    @staticmethod
    def _campos(pago: Pago) -> dict:
        return {
            "socio_id": pago.socio.id,
            "plan_id": pago.plan_id,
            "valor": pago.valor,
            "duracion_dias": pago.duracion_dias,
            "medio": pago.medio.value,
            "referencia": pago.referencia,
            "fecha_inicio": pago.fecha_inicio,
            "fecha_vencimiento": pago.fecha_vencimiento,
            "registrado_por_id": pago.registrado_por.id,
            "registrado_en": pago.registrado_en,
            "estado": pago.estado.value,
            "fecha_anulacion": pago.fecha_anulacion,
            "anulado_por_id": pago.anulado_por.id if pago.anulado_por else None,
            "motivo_anulacion": pago.motivo_anulacion,
        }
