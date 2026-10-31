"""Backend de correo que simula el SMTP del hosting caído (solo para pruebas)."""

import smtplib

from django.core.mail.backends.base import BaseEmailBackend


class CorreoCaido(BaseEmailBackend):
    def send_messages(self, email_messages):
        raise smtplib.SMTPServerDisconnected("Connection unexpectedly closed")
