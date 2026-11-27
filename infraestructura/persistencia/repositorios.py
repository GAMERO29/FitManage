"""Adaptadores de los puertos SocioRepositorio, PlanRepositorio y PagoRepositorio (paga DT-02)."""

from __future__ import annotations

from uuid import UUID

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from dominio.errores import DocumentoDuplicado, ReferenciaDuplicada, SocioConPagos
from dominio.modelos import (
    EstadoPago,
    Pago,
    Plan,
    Socio,
    TipoDocumento,
    Usuario,
)
from infraestructura.persistencia.mapeo import a_pago, a_socio, a_usuario
from infraestructura.persistencia.models import PagoModelo, PlanModelo, SocioModelo, UsuarioModelo

RESTRICCION_REFERENCIA = "referencia_vigente_unica"
RESTRICCION_DOCUMENTO = "socio_documento_unico"  # RN-01


class UsuarioRepositorioORM:
    """Contexto Acceso del personal: es el único que escribe en la tabla usuarios (paga DT-11)."""

    def obtener(self, usuario_id: UUID) -> Usuario | None:
        m = UsuarioModelo.objects.filter(id=usuario_id).first()
        return a_usuario(m) if m else None

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
        return a_socio(m) if m else None

    def guardar(self, socio: Socio) -> None:
        try:
            with transaction.atomic():  # punto de guardado: la transacción de afuera sigue sana
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
        except IntegrityError as error:
            # PostgreSQL nombra la restricción; SQLite nombra las columnas.
            if RESTRICCION_DOCUMENTO in str(error) or "socios.numero_documento" in str(error):
                raise DocumentoDuplicado() from error
            raise

    def eliminar(self, socio: Socio) -> None:
        """La regla la revisa el servicio; la llave PROTECT de `pagos` es la segunda barrera."""
        try:
            SocioModelo.objects.filter(id=socio.id).delete()
        except ProtectedError as error:
            raise SocioConPagos() from error


class PlanRepositorioORM:
    def obtener(self, plan_id: UUID) -> Plan | None:
        m = PlanModelo.objects.filter(id=plan_id).first()
        if m is None:
            return None
        return Plan(m.nombre, m.duracion_dias, m.precio, m.activo, id=m.id)

    def todos(self) -> list[Plan]:
        return [
            Plan(m.nombre, m.duracion_dias, m.precio, m.activo, id=m.id)
            for m in PlanModelo.objects.order_by("duracion_dias", "nombre")
        ]

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
    def tiene_pagos(self, socio: Socio) -> bool:
        return PagoModelo.objects.filter(socio_id=socio.id).exists()

    def vigentes_de(self, socio: Socio) -> list[Pago]:
        consulta = PagoModelo.objects.select_related(
            "socio", "registrado_por", "anulado_por"
        ).filter(socio_id=socio.id, estado=EstadoPago.VIGENTE.value)
        return [a_pago(m) for m in consulta]

    def existe_referencia_vigente(self, referencia: str) -> bool:
        return PagoModelo.objects.filter(
            referencia=referencia, estado=EstadoPago.VIGENTE.value
        ).exists()

    def obtener(self, pago_id: UUID) -> Pago | None:
        m = (
            PagoModelo.objects.select_related("socio", "registrado_por", "anulado_por")
            .filter(id=pago_id)
            .first()
        )
        return a_pago(m) if m else None

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
