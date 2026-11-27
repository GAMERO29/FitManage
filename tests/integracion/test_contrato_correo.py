"""Software III, Guía 09: el mismo contrato de CorreoSaliente para todas sus variantes (LSP).

Contrato (dominio/puertos.py):
- Precondición: un destinatario con «@». Si no, DatosInvalidos y no se intenta enviar.
- Poscondición: si `enviar` retorna, el servidor aceptó el mensaje para ese destinatario.
- Si el servidor no responde o no acepta el mensaje: CorreoNoDisponible, nunca éxito.
Variantes: el doble en memoria y CorreoDjango sobre tres backends (memoria de Django, servidor
caído y servidor que no entrega nada).
"""

import pytest
from django.core import mail
from dobles import CorreoEnMemoria

from dominio.errores import CorreoNoDisponible, DatosInvalidos
from infraestructura.correo import CorreoDjango

LOCMEM = "django.core.mail.backends.locmem.EmailBackend"
CAIDO = "correo_caido.CorreoCaido"
NO_ENTREGA = "correo_caido.CorreoQueNoEntrega"


class Variante:
    """Envuelve cada implementación con una forma común de leer lo que de verdad salió."""

    def __init__(self, nombre, correo, entregados):
        self.nombre, self.correo, self._entregados = nombre, correo, entregados

    def entregados(self):
        return self._entregados()


@pytest.fixture(params=["memoria", "django"])
def sana(request, settings):
    if request.param == "memoria":
        doble = CorreoEnMemoria()
        return Variante("memoria", doble, lambda: [m.destinatario for m in doble.enviados])
    settings.EMAIL_BACKEND = LOCMEM
    return Variante("django", CorreoDjango(), lambda: [d for m in mail.outbox for d in m.to])


@pytest.fixture(params=["memoria-caido", "django-caido", "django-no-entrega"])
def fallida(request, settings):
    if request.param == "memoria-caido":
        return Variante(request.param, CorreoEnMemoria(falla=True), lambda: [])
    settings.EMAIL_BACKEND = CAIDO if request.param == "django-caido" else NO_ENTREGA
    return Variante(request.param, CorreoDjango(), lambda: [])


def test_si_retorna_el_mensaje_salio_para_ese_destinatario(sana):
    sana.correo.enviar("laura@demo.local", "Asunto", "Cuerpo")
    assert sana.entregados() == ["laura@demo.local"]


@pytest.mark.parametrize("destinatario", ["", "   ", "laura.demo.local"])
def test_sin_destinatario_valido_no_hay_exito(sana, destinatario):
    with pytest.raises(DatosInvalidos):
        sana.correo.enviar(destinatario, "Asunto", "Cuerpo")
    assert sana.entregados() == []


def test_un_servidor_que_no_acepta_el_mensaje_nunca_es_exito(fallida):
    with pytest.raises(CorreoNoDisponible):
        fallida.correo.enviar("laura@demo.local", "Asunto", "Cuerpo")
