"""Tablas de PostgreSQL. Son detalles del adaptador: el dominio nunca las importa."""

from __future__ import annotations

import uuid

from django.db import models
from django.db.models import F, Q


class SocioModelo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo_documento = models.CharField(max_length=10)
    numero_documento = models.CharField(max_length=20)
    nombres = models.CharField(max_length=80)
    apellidos = models.CharField(max_length=80)
    telefono = models.CharField(max_length=10)
    autorizacion_datos = models.DateTimeField()

    class Meta:
        db_table = "socios"
        constraints = [
            models.UniqueConstraint(
                fields=["tipo_documento", "numero_documento"], name="socio_documento_unico"
            ),  # RN-01
        ]


class PlanModelo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=40)
    duracion_dias = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "planes"


class UsuarioModelo(models.Model):
    """Cuentas del personal; solo el contexto Acceso del personal escribe aquí (DT-11)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=80)
    correo = models.EmailField(unique=True)
    rol = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)
    # Credenciales (Guía 7): hash de Django, nunca la contraseña; bloqueo de RF-09.
    clave_hash = models.CharField(max_length=128, default="", blank=True)
    intentos_fallidos = models.PositiveSmallIntegerField(default=0)
    bloqueada_hasta = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "usuarios"


class RenovacionModelo(models.Model):
    """Token de renovación de 8 horas por dispositivo (ADR N.° 06). Solo se guarda su SHA-256."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        UsuarioModelo, on_delete=models.CASCADE, related_name="renovaciones"
    )
    huella = models.CharField(max_length=64, unique=True)
    vence = models.DateTimeField()
    revocada = models.BooleanField(default=False)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "renovaciones"


class IdempotenciaModelo(models.Model):
    """Respuesta guardada por `Idempotency-Key`: un doble clic no crea dos pagos (PA-11)."""

    clave = models.UUIDField(primary_key=True)
    usuario = models.ForeignKey(UsuarioModelo, on_delete=models.CASCADE)
    estado_http = models.PositiveSmallIntegerField(default=0)
    cuerpo = models.JSONField(default=dict)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "idempotencia"


class PagoModelo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    socio = models.ForeignKey(SocioModelo, on_delete=models.PROTECT, related_name="pagos")
    plan = models.ForeignKey(PlanModelo, on_delete=models.PROTECT, related_name="pagos")
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    duracion_dias = models.PositiveIntegerField()
    medio = models.CharField(max_length=20)
    # NULL a propósito: el índice único parcial (RN-06) solo aplica a referencias no nulas,
    # y los pagos en efectivo no tienen referencia. Una cadena vacía chocaría entre sí.
    referencia = models.CharField(max_length=40, null=True, blank=True)  # nosemgrep
    fecha_inicio = models.DateField()
    fecha_vencimiento = models.DateField()
    registrado_por = models.ForeignKey(
        UsuarioModelo, on_delete=models.PROTECT, related_name="pagos_registrados"
    )
    registrado_en = models.DateTimeField()
    estado = models.CharField(max_length=10, default="VIGENTE")
    fecha_anulacion = models.DateTimeField(null=True, blank=True)
    anulado_por = models.ForeignKey(
        UsuarioModelo,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pagos_anulados",
    )
    # NULL distingue «nunca se anuló» de un motivo, y la migración ya está en producción.
    motivo_anulacion = models.TextField(null=True, blank=True)  # nosemgrep

    class Meta:
        db_table = "pagos"
        indexes = [models.Index(fields=["socio", "estado"], name="pago_socio_estado")]
        constraints = [
            # RN-06 y DT-01: la base de datos impide dos pagos vigentes con la misma referencia.
            models.UniqueConstraint(
                fields=["referencia"],
                condition=Q(estado="VIGENTE") & Q(referencia__isnull=False),
                name="referencia_vigente_unica",
            ),
            models.CheckConstraint(
                condition=Q(fecha_vencimiento__gte=F("fecha_inicio")),
                name="vencimiento_no_anterior_al_inicio",
            ),
            # Guía II-03, DT-30: la base ya no acepta un estado inventado ni una anulación a medias.
            models.CheckConstraint(
                condition=Q(estado__in=["VIGENTE", "ANULADO"]), name="estado_de_pago_conocido"
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        estado="VIGENTE",
                        fecha_anulacion__isnull=True,
                        anulado_por__isnull=True,
                        motivo_anulacion__isnull=True,
                    )
                    | (
                        Q(
                            estado="ANULADO",
                            fecha_anulacion__isnull=False,
                            anulado_por__isnull=False,
                            motivo_anulacion__isnull=False,
                        )
                        & ~Q(motivo_anulacion="")
                    )
                ),
                name="anulacion_completa_o_ninguna",
            ),
        ]


class EventoAuditoriaModelo(models.Model):
    """Rastro de solo inserción (ADR N.° 19, DT-14). Un disparador rechaza UPDATE y DELETE.

    Guarda ids y valores del negocio, nunca el documento ni el teléfono del socio.
    """

    id = models.BigAutoField(primary_key=True)
    ocurrido_en = models.DateTimeField()
    tipo = models.CharField(max_length=30)
    actor = models.ForeignKey(
        UsuarioModelo, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    # Copia del nombre: si la cuenta cambia de nombre, el rastro sigue diciendo quién fue.
    actor_nombre = models.CharField(max_length=80)
    entidad_id = models.UUIDField()
    socio_id = models.UUIDField(null=True, blank=True)
    detalle = models.JSONField(default=dict)

    class Meta:
        db_table = "auditoria"
        indexes = [models.Index(fields=["ocurrido_en"], name="auditoria_ocurrido_en")]
