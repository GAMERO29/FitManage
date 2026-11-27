"""Adaptador del puerto CorreoSaliente sobre el correo de Django (SMTP del hosting, DAD 8.2)."""

from __future__ import annotations

import smtplib

from django.conf import settings
from django.core.mail import send_mail

from dominio.errores import CorreoNoDisponible
from dominio.puertos import exigir_destinatario


class CorreoDjango:
    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        destinatario = exigir_destinatario(destinatario)
        try:
            enviados = send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [destinatario])
        except (smtplib.SMTPException, OSError) as error:
            raise CorreoNoDisponible("El servidor de correo no respondió.") from error
        # send_mail devuelve cuántos mensajes salieron. Antes se ignoraba y un 0 contaba como
        # éxito: la API respondía 202 «enviado» sin haber enviado nada (Software III, Guía 09).
        if enviados != 1:
            raise CorreoNoDisponible("El servidor de correo no aceptó el mensaje.")
