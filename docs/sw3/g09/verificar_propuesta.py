"""Software III · Guía 09: los subtipos de la IA contra el contrato de CorreoSaliente.

Precondición del contrato: cualquier dirección con «@». Poscondición: si retorna, salió.
Uso:  python3 docs/sw3/g09/verificar_propuesta.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from propuesta_ia import NotificadorConsola, NotificadorNulo, NotificadorSMTP  # noqa: E402


class ClienteSMTPEnMemoria:
    def __init__(self):
        self.salidos = []

    def sendmail(self, remitente, destinatarios, mensaje):
        self.salidos += destinatarios


def revisar(nombre, ok, detalle):
    print(f"{'PASA ' if ok else 'FALLA'} {nombre}: {detalle}")


cliente = ClienteSMTPEnMemoria()
smtp = NotificadorSMTP(cliente)
try:
    smtp.enviar("laura@demo.local", "Asunto", "Cuerpo")
    revisar("SMTP, precondición", True, "acepta cualquier dirección con @")
except ValueError as error:
    revisar("SMTP, precondición", False, f"exige más que el contrato: {error}")

nulo = NotificadorNulo()
revisar(
    "Nulo, poscondición",
    False,
    f"enviar() devolvió {nulo.enviar('laura@demo.local', 'A', 'C')} y no salió ningún mensaje",
)
consola = NotificadorConsola()
salida = consola.enviar("", "A", "C")
revisar("Consola, precondición", salida is not True, f"destinatario vacío devolvió {salida}")
