"""Acceso del personal: JWT, bloqueo tras 5 intentos y renovación con cookie (ADR N.° 06)."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from apoyo_api import AHORA, CLAVE
from django.conf import settings
from dobles import RelojFijo

from infraestructura.api import contenedor, tokens

LOGIN = "/api/v1/auth/token"
RENOVACION = "/api/v1/auth/renovacion"


def test_inicio_de_sesion_entrega_jwt_y_cookie_de_renovacion(api, gimnasio):
    r = api.post(LOGIN, {"correo": "laura@gimnasio-demo.co", "contrasena": CLAVE})
    assert r.status_code == 200
    cuerpo = r.json()
    assert (cuerpo["tipo"], cuerpo["expiraEn"], cuerpo["rol"]) == ("Bearer", 900, "RECEPCIONISTA")
    claims = tokens.leer_acceso(cuerpo["tokenAcceso"])
    assert claims["sub"] == str(gimnasio["laura"].id) and claims["rol"] == "RECEPCIONISTA"
    assert jwt.get_unverified_header(cuerpo["tokenAcceso"])["kid"] == settings.JWT_KID
    cookie = r.cookies["fm_renovacion"]
    assert cookie["httponly"] and cookie["secure"] and cookie["samesite"] == "Strict"
    assert cookie["path"] == RENOVACION
    assert "contrasena" not in r.content.decode()


def test_el_correo_no_distingue_mayusculas(api):
    assert (
        api.post(LOGIN, {"correo": "Laura@Gimnasio-Demo.co", "contrasena": CLAVE}).status_code
        == 200
    )


@pytest.mark.parametrize("correo", ["laura@gimnasio-demo.co", "nadie@gimnasio-demo.co"])
def test_credenciales_incorrectas_no_dicen_cual_fallo(api, correo):
    r = api.post(LOGIN, {"correo": correo, "contrasena": "otraclave1"})
    assert r.status_code == 401
    assert r.json()["codigo"] == "CREDENCIALES_INVALIDAS"


def test_cuerpo_incompleto_es_400_segun_el_contrato(api):
    r = api.post(LOGIN, {"correo": "laura@gimnasio-demo.co"})
    assert r.status_code == 400
    assert r.json()["codigo"] == "SOLICITUD_INVALIDA"


def test_quinto_intento_fallido_bloquea_15_minutos(api, monkeypatch):
    """PA-10: cinco intentos fallidos → cuenta bloqueada 15 minutos."""
    fallo = {"correo": "laura@gimnasio-demo.co", "contrasena": "equivocada"}
    for _ in range(4):
        assert api.post(LOGIN, fallo).status_code == 401
    r = api.post(LOGIN, fallo)
    assert r.status_code == 423 and r["Retry-After"] == "900"
    correcta = {"correo": "laura@gimnasio-demo.co", "contrasena": CLAVE}
    assert api.post(LOGIN, correcta).status_code == 423
    monkeypatch.setattr(contenedor, "reloj", lambda: RelojFijo(AHORA + timedelta(minutes=15)))
    assert api.post(LOGIN, correcta).status_code == 200


def test_iniciar_sesion_reinicia_el_contador_de_fallos(api):
    fallo = {"correo": "laura@gimnasio-demo.co", "contrasena": "equivocada"}
    for _ in range(4):
        api.post(LOGIN, fallo)
    api.post(LOGIN, {"correo": "laura@gimnasio-demo.co", "contrasena": CLAVE})
    assert api.post(LOGIN, fallo).status_code == 401  # vuelve a contar desde cero


def test_renovacion_rota_la_cookie(api, client):
    api.post(LOGIN, {"correo": "laura@gimnasio-demo.co", "contrasena": CLAVE})
    primera = client.cookies["fm_renovacion"].value
    r = api.post(RENOVACION)
    assert r.status_code == 200 and r.json()["tokenAcceso"]
    assert client.cookies["fm_renovacion"].value != primera
    client.cookies["fm_renovacion"] = primera
    assert api.post(RENOVACION).status_code == 401  # la cookie usada quedó revocada


def test_renovacion_sin_cookie_es_401(api):
    assert api.post(RENOVACION).status_code == 401


def test_una_cuenta_desactivada_no_renueva(api, client, gimnasio):
    from infraestructura.persistencia.models import UsuarioModelo

    api.post(LOGIN, {"correo": "laura@gimnasio-demo.co", "contrasena": CLAVE})
    UsuarioModelo.objects.filter(id=gimnasio["laura"].id).update(activo=False)
    assert api.post(RENOVACION).status_code == 401


def _token(clave=None, algoritmo="HS256", **cambios):
    ahora = datetime.now(UTC)
    claims = {
        "sub": "7b1e9a2c-0000-4000-8000-000000000000",
        "rol": "ADMINISTRADOR",
        "iss": "fitmanage",
        "aud": "fitmanage-api",
        "iat": int(ahora.timestamp()),
        "exp": int((ahora + timedelta(minutes=15)).timestamp()),
        "jti": "x",
    } | cambios
    return jwt.encode(claims, clave or settings.JWT_CLAVE, algorithm=algoritmo)


@pytest.mark.parametrize(
    "encabezado",
    [
        None,
        "Token abc",
        "Bearer",
        "Bearer no-es-un-jwt",
        f"Bearer {_token(clave='otra-clave-que-no-es-la-del-servidor-1234')}",
        f"Bearer {_token(exp=1)}",
        f"Bearer {_token(aud='otra-api')}",
        f"Bearer {_token(iss='otro-emisor')}",
        f"Bearer {_token(sub='no-es-un-uuid')}",
    ],
    ids=["sin", "esquema", "vacio", "basura", "firma", "vencido", "aud", "iss", "sub"],
)
def test_todo_token_invalido_es_401(client, gimnasio, encabezado):
    extra = {"HTTP_AUTHORIZATION": encabezado} if encabezado else {}
    r = client.get("/api/v1/planes", **extra)
    assert r.status_code == 401
    assert r["WWW-Authenticate"].startswith("Bearer")


def test_se_rechaza_alg_none(client, gimnasio):
    sin_firma = jwt.encode(
        {"sub": str(gimnasio["carlos"].id), "rol": "ADMINISTRADOR"}, None, algorithm="none"
    )
    assert client.get("/api/v1/planes", HTTP_AUTHORIZATION=f"Bearer {sin_firma}").status_code == 401


def test_un_token_de_cuenta_desactivada_deja_de_servir(api, gimnasio):
    from infraestructura.persistencia.models import UsuarioModelo

    api.como("laura@gimnasio-demo.co")
    UsuarioModelo.objects.filter(id=gimnasio["laura"].id).update(activo=False)
    assert api.get("/api/v1/planes").status_code == 401


def test_el_rol_sale_de_la_base_y_no_del_token(api, gimnasio):
    """ADR N.° 06: un token con rol ADMINISTRADOR no sirve si en la base es recepcionista."""
    falso_admin = _token(sub=str(gimnasio["laura"].id), rol="ADMINISTRADOR")
    api.token = falso_admin
    r = api.get("/api/v1/reportes/ingresos", {"desde": "2026-10-01", "hasta": "2026-10-07"})
    assert r.status_code == 403
