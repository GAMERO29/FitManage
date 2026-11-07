"""Primer arranque en producción (Guía 16): planes iniciales y la primera cuenta de administrador.

El servicio web gratuito de Render no tiene Shell, así que sin esto la base de producción queda
sin planes ni personal y nadie puede iniciar sesión. Corre en cada arranque (`arrancar.sh`) y es
idempotente: nunca modifica un plan ni una cuenta que ya existan.

La cuenta sale de tres variables de entorno que se configuran en el panel del PaaS:
FITMANAGE_ADMIN_NOMBRE, FITMANAGE_ADMIN_CORREO y FITMANAGE_ADMIN_CLAVE. La clave nunca se
imprime, ni siquiera en un error.
"""

from __future__ import annotations

import os
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from infraestructura.persistencia.models import PlanModelo, UsuarioModelo

# Precios de referencia de un gimnasio de barrio (los mismos de las pruebas de carga, QA-01).
PLANES_INICIALES = (
    ("Diario", 1, 8000),
    ("Quincenal", 15, 45000),
    ("Mensual", 30, 75000),
    ("Trimestral", 90, 200000),
)
LONGITUD_MINIMA_CLAVE = 12


class Command(BaseCommand):
    help = "Crea los planes iniciales y la primera cuenta de administrador si aún no existen."

    def handle(self, *args, **opciones) -> None:
        with transaction.atomic():
            self._planes()
            self._administrador()

    def _planes(self) -> None:
        if PlanModelo.objects.exists():
            self.stdout.write("Planes: ya existen, no se tocan.")
            return
        for nombre, dias, precio in PLANES_INICIALES:
            PlanModelo.objects.create(nombre=nombre, duracion_dias=dias, precio=Decimal(precio))
        self.stdout.write(f"Planes: se crearon {len(PLANES_INICIALES)}.")

    def _administrador(self) -> None:
        if UsuarioModelo.objects.filter(rol="ADMINISTRADOR").exists():
            self.stdout.write("Administrador: ya existe, no se toca.")
            return
        nombre = os.environ.get("FITMANAGE_ADMIN_NOMBRE", "").strip()
        correo = os.environ.get("FITMANAGE_ADMIN_CORREO", "").strip().lower()
        clave = os.environ.get("FITMANAGE_ADMIN_CLAVE", "")
        if not (nombre and correo and clave):
            self.stdout.write(
                "Administrador: no hay ninguno y faltan FITMANAGE_ADMIN_NOMBRE, "
                "FITMANAGE_ADMIN_CORREO o FITMANAGE_ADMIN_CLAVE. Nadie podrá iniciar sesión."
            )
            return
        if len(clave) < LONGITUD_MINIMA_CLAVE:
            raise CommandError(
                f"FITMANAGE_ADMIN_CLAVE debe tener al menos {LONGITUD_MINIMA_CLAVE} caracteres."
            )
        if UsuarioModelo.objects.filter(correo=correo).exists():
            raise CommandError("Ya existe una cuenta con ese correo y no es de administrador.")
        UsuarioModelo.objects.create(
            nombre=nombre, correo=correo, rol="ADMINISTRADOR", clave_hash=make_password(clave)
        )
        self.stdout.write(f"Administrador: se creó la cuenta de {nombre}.")
