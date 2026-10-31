"""Frontera con la única dependencia externa: el SMTP del hosting (DAD 8.2).

El correo se aísla en el backend de Django, no en el caso de uso: el servicio, el repositorio
y la base son reales; lo único falso es el servidor que recibiría el mensaje.
"""

import uuid

import pytest
from django.conf import settings
from django.core import mail, signing

from infraestructura.persistencia.models import UsuarioModelo

RUTA = "/api/v1/personal/{}/restablecimiento"


@pytest.fixture
def administracion(api):
    return api.como("carlos@gimnasio-demo.co")


def test_las_pruebas_nunca_usan_el_smtp_real():
    assert settings.EMAIL_BACKEND == "django.core.mail.backends.locmem.EmailBackend"


def test_envia_un_enlace_firmado_que_vence_en_30_minutos(administracion, gimnasio):
    laura = gimnasio["laura"]
    r = administracion.post(RUTA.format(laura.id))
    assert r.status_code == 202
    assert r.json() == {"enviadoA": "l****@gimnasio-demo.co", "venceEn": 1800}
    [mensaje] = mail.outbox
    assert mensaje.to == ["laura@gimnasio-demo.co"]
    token = mensaje.body.split("/restablecer/")[1].split("/")[0]
    firmado = signing.TimestampSigner(salt="fitmanage.restablecer")
    assert firmado.unsign(token, max_age=1800) == str(laura.id)


def test_si_el_smtp_esta_caido_responde_503_y_la_cuenta_no_cambia(
    administracion, gimnasio, settings
):
    settings.EMAIL_BACKEND = "correo_caido.CorreoCaido"
    antes = UsuarioModelo.objects.values().get(id=gimnasio["laura"].id)
    r = administracion.post(RUTA.format(gimnasio["laura"].id))
    assert r.status_code == 503 and r.json()["codigo"] == "CORREO_NO_DISPONIBLE"
    assert UsuarioModelo.objects.values().get(id=gimnasio["laura"].id) == antes
    assert mail.outbox == []


def test_cuenta_inexistente_es_404(administracion):
    assert administracion.post(RUTA.format(uuid.uuid4())).status_code == 404
    assert mail.outbox == []


def test_la_recepcionista_no_puede_restablecer(api, gimnasio):
    r = api.como("laura@gimnasio-demo.co").post(RUTA.format(gimnasio["carlos"].id))
    assert r.status_code == 403 and mail.outbox == []
