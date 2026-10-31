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
    """Provisional hasta el módulo cuentas (DT-11)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=80)
    correo = models.EmailField(unique=True)
    rol = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "usuarios"


class PagoModelo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    socio = models.ForeignKey(SocioModelo, on_delete=models.PROTECT, related_name="pagos")
    plan = models.ForeignKey(PlanModelo, on_delete=models.PROTECT, related_name="pagos")
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    duracion_dias = models.PositiveIntegerField()
    medio = models.CharField(max_length=20)
    referencia = models.CharField(max_length=40, null=True, blank=True)
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
    motivo_anulacion = models.TextField(null=True, blank=True)

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
        ]
