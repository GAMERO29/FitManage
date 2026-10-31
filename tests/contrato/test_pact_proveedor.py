"""Verificación del proveedor: la API real cumple el pact que escribió la vista móvil.

El pact (`vista-movil/pacts/VistaMovil-FitManageAPI.json`) lo genera el consumidor con
`npm run test:pact`. Aquí se levanta Django de verdad (`live_server`) sobre la base efímera y
pact-python repite cada interacción. Si alguien cambia un campo de `EstadoPublico` que la vista
móvil usa, esta prueba falla antes de llegar a `main`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from apoyo_api import AHORA, sembrar
from dobles import RelojFijo

from infraestructura.api import contenedor, tokens
from infraestructura.persistencia.models import SocioModelo

PACT = (
    Path(__file__).resolve().parents[2] / "vista-movil" / "pacts" / "VistaMovil-FitManageAPI.json"
)
TOKEN_DEL_CONSUMIDOR = "eyJhbGciOiJIUzI1NiJ9.token-de-prueba.firma"

pact = pytest.importorskip("pact")


@pytest.fixture
def proveedor(transactional_db, live_server, monkeypatch, settings):
    monkeypatch.setenv("PACT_DO_NOT_TRACK", "true")  # sin telemetría de Pact en la suite
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    monkeypatch.setattr(contenedor, "reloj", lambda: RelojFijo(AHORA))
    datos = sembrar()
    leer_real = tokens.leer_acceso

    def leer(token: str) -> dict:
        # El consumidor no puede conocer un JWT válido del proveedor: su token de ejemplo se
        # traduce a una sesión real de Laura. Cualquier otro token pasa por la validación real.
        if token == TOKEN_DEL_CONSUMIDOR:
            return leer_real(tokens.emitir_acceso(datos["laura"]))
        return leer_real(token)

    monkeypatch.setattr(tokens, "leer_acceso", leer)
    return live_server.url


def _socia_activa(**_) -> None:
    assert SocioModelo.objects.filter(numero_documento="1090123456").exists()


def _sin_socio(**_) -> None:
    SocioModelo.objects.filter(numero_documento="1111111111").delete()


def test_la_api_cumple_el_pact_de_la_vista_movil(proveedor):
    verificador = (
        pact.Verifier("FitManageAPI")
        .add_source(str(PACT))
        .add_transport(url=proveedor)
        .state_handler(
            {
                "la socia CC 1090123456 tiene membresía activa": _socia_activa,
                "no hay ningún socio con el documento CC 1111111111": _sin_socio,
            },
            teardown=False,
        )
    )
    verificador.verify()  # lanza una excepción con el detalle si alguna interacción no cumple
