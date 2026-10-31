"""Adaptador del puerto CorreoSaliente sobre el correo de Django (SMTP del hosting, DAD 8.2)."""

from __future__ import annotations

import smtplib

from django.conf import settings
from django.core.mail import send_mail

from dominio.errores import CorreoNoDisponible


class CorreoDjango:
    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        try:
            send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [destinatario])
        except (smtplib.SMTPException, OSError) as error:
            raise CorreoNoDisponible("El servidor de correo no respondió.") from error
