"""Salida de la IA, copiada sin cambios (fragmento relevante). NO se usa en el código de FitManage.

Prompt: «Diseña con herencia las formas de enviar correo de FitManage: SMTP en producción, consola
en desarrollo y una variante que no envíe nada para las pruebas.»
"""

from abc import ABC, abstractmethod


class Notificador(ABC):
    def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> bool:
        mensaje = self.formatear(asunto, cuerpo)
        return self._entregar(destinatario, mensaje)

    def formatear(self, asunto: str, cuerpo: str) -> str:
        return f"{asunto}\n\n{cuerpo}"

    @abstractmethod
    def _entregar(self, destinatario: str, mensaje: str) -> bool: ...


class NotificadorSMTP(Notificador):
    def __init__(self, cliente):
        self.cliente = cliente

    def _entregar(self, destinatario, mensaje):
        if not destinatario.endswith("@gimnasio.co"):  # solo correos del gimnasio
            raise ValueError("Dominio no permitido")
        self.cliente.sendmail("no-responder@gimnasio.co", [destinatario], mensaje)
        return True


class NotificadorConsola(Notificador):
    def _entregar(self, destinatario, mensaje):
        print(mensaje)
        return True


class NotificadorNulo(Notificador):
    def _entregar(self, destinatario, mensaje):
        return True  # no hace nada, para pruebas
