"""Backend de correo que simula el SMTP del hosting caído (solo para pruebas)."""

import smtplib

from django.core.mail.backends.base import BaseEmailBackend


class CorreoCaido(BaseEmailBackend):
    def send_messages(self, email_messages):
        raise smtplib.SMTPServerDisconnected("Connection unexpectedly closed")


class CorreoQueNoEntrega(BaseEmailBackend):
    """Simula un servidor que responde sin entregar nada: Django recibe 0 mensajes enviados.

    Es lo que hace el backend SMTP de Django cuando el mensaje se queda sin destinatarios.
    """

    def send_messages(self, email_messages):
        return 0
