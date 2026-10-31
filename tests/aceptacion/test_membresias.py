"""Pasos de los escenarios de aceptación (UAT) del DDS, contra la API y la base reales."""

import uuid
from datetime import datetime, timedelta

import pytest
from apoyo_api import CLAVE
from dobles import RelojFijo
from pytest_bdd import given, parsers, scenarios, then, when

from dominio.modelos import ZONA_HORARIA
from infraestructura.api import contenedor
from infraestructura.persistencia.models import PagoModelo, SocioModelo

# La base efímera se crea antes del escenario, no a mitad de un paso.
pytestmark = pytest.mark.django_db

scenarios("membresias.feature")

CORREOS = {
    "la recepcionista": "laura@gimnasio-demo.co",
    "el administrador": "carlos@gimnasio-demo.co",
}


@pytest.fixture
def contexto():
    return {}


def _documento(texto: str) -> tuple[str, str]:
    tipo, numero = texto.split()
    return tipo, numero


def _ultimo_pago(numero: str) -> PagoModelo:
    return PagoModelo.objects.filter(socio__numero_documento=numero, estado="VIGENTE").latest(
        "fecha_inicio"
    )


@given(parsers.parse("que hoy es {fecha} a las {hora} en Colombia"))
def hoy_es(api, monkeypatch, fecha, hora):
    """Pide `api` primero para que el reloj de los datos de prueba no pise esta fecha."""
    momento = datetime.fromisoformat(f"{fecha}T{hora}").replace(tzinfo=ZONA_HORARIA)
    monkeypatch.setattr(contenedor, "reloj", lambda: RelojFijo(momento))


@given(parsers.parse("que {quien} inició sesión"))
def inicio_sesion(api, quien):
    api.como(CORREOS[quien])


def _pagar(api, contexto, plan, medio, documento, referencia=None, gimnasio=None, clave=None):
    tipo, numero = _documento(documento)
    cuerpo = {
        "tipoDocumento": tipo,
        "numeroDocumento": numero,
        "planId": str(gimnasio[plan.lower()].id),
        "medio": medio,
    } | ({"referencia": referencia} if referencia else {})
    contexto["respuesta"] = api.post(
        "/api/v1/pagos", cuerpo, {"Idempotency-Key": clave or str(uuid.uuid4())}
    )
    return contexto["respuesta"]


@when(parsers.parse("registra un socio con el documento {documento}"))
def registrar_socio(api, contexto, documento):
    tipo, numero = _documento(documento)
    contexto["respuesta"] = api.post(
        "/api/v1/socios",
        {
            "tipoDocumento": tipo,
            "numeroDocumento": numero,
            "nombres": "Otra",
            "apellidos": "Persona",
            "telefono": "3000000009",
            "autorizaTratamientoDatos": True,
        },
    )


@when(parsers.parse("registra un pago {plan} en efectivo para {documento}"))
def pago_efectivo(api, contexto, gimnasio, plan, documento):
    _pagar(api, contexto, plan, "EFECTIVO", documento, gimnasio=gimnasio)


@when(parsers.parse("registra un pago {plan} por {medio} con referencia {ref} para {documento}"))
def pago_con_referencia(api, contexto, gimnasio, plan, medio, ref, documento):
    _pagar(api, contexto, plan, medio, documento, ref, gimnasio)


@when(parsers.parse("envía dos veces el mismo pago {plan} en efectivo para {documento}"))
def doble_clic(api, contexto, gimnasio, plan, documento):
    clave = str(uuid.uuid4())
    contexto["primera"] = _pagar(
        api, contexto, plan, "EFECTIVO", documento, gimnasio=gimnasio, clave=clave
    )
    contexto["segunda"] = _pagar(
        api, contexto, plan, "EFECTIVO", documento, gimnasio=gimnasio, clave=clave
    )


@when(parsers.parse("consulta el estado de {documento}"))
def consultar(api, contexto, documento):
    tipo, numero = _documento(documento)
    contexto["respuesta"] = api.get(f"/api/v1/estados/{tipo}/{numero}")


@when(parsers.parse("intenta anular el último pago de {documento}"))
def intenta_anular(api, contexto, documento):
    pago = _ultimo_pago(_documento(documento)[1])
    contexto["respuesta"] = api.patch(
        f"/api/v1/pagos/{pago.id}", {"estado": "ANULADO", "motivo": "Intento de anulación"}
    )


@when("intenta abrir el reporte de ingresos de octubre")
def abrir_reporte(api, contexto):
    contexto["respuesta"] = api.get(
        "/api/v1/reportes/ingresos", {"desde": "2026-10-01", "hasta": "2026-10-31"}
    )


@given(parsers.parse('que anuló el último pago de {documento} porque "{motivo}"'))
@when(parsers.parse('anula el último pago de {documento} porque "{motivo}"'))
def anular(api, contexto, documento, motivo):
    pago = _ultimo_pago(_documento(documento)[1])
    contexto["pago_id"] = pago.id
    contexto["motivo"] = motivo
    contexto["respuesta"] = api.patch(
        f"/api/v1/pagos/{pago.id}", {"estado": "ANULADO", "motivo": motivo}
    )
    assert contexto["respuesta"].status_code == 200


@when(parsers.parse("Laura escribe mal su contraseña {veces:d} veces"))
def fallos(api, contexto, veces):
    for _ in range(veces):
        contexto["respuesta"] = api.post(
            "/api/v1/auth/token", {"correo": "laura@gimnasio-demo.co", "contrasena": "equivocada"}
        )


@then(parsers.parse("la respuesta es {status:d} con el código {codigo}"))
def respuesta_con_codigo(contexto, status, codigo):
    assert contexto["respuesta"].status_code == status
    assert contexto["respuesta"].json()["codigo"] == codigo


@then(parsers.parse("la respuesta es {status:d}"))
def respuesta(contexto, status):
    assert contexto["respuesta"].status_code == status


@then("sigue existiendo un solo socio con ese documento")
def un_solo_socio():
    assert SocioModelo.objects.filter(numero_documento="1090123456").count() == 1


@then(parsers.parse("el pago inicia el {inicio} y vence el {vence}"))
def fechas(contexto, inicio, vence):
    cuerpo = contexto["respuesta"].json()
    assert (cuerpo["inicia"], cuerpo["vence"]) == (inicio, vence)


@then(parsers.parse("el estado es {estado} con {dias:d} día restante"))
def estado_con_dias(contexto, estado, dias):
    cuerpo = contexto["respuesta"].json()
    assert (cuerpo["estado"], cuerpo["diasRestantes"]) == (estado, dias)


@then("el pago queda ANULADO con el motivo guardado")
def pago_anulado(contexto):
    guardado = PagoModelo.objects.get(id=contexto["pago_id"])
    assert (guardado.estado, guardado.motivo_anulacion) == ("ANULADO", contexto["motivo"])


@then(parsers.parse("el estado de {documento} es {estado}"))
def estado_es(api, documento, estado):
    tipo, numero = _documento(documento)
    assert api.get(f"/api/v1/estados/{tipo}/{numero}").json()["estado"] == estado


@then("ni con la contraseña correcta puede entrar hasta 15 minutos después")
def bloqueada(api, reloj, monkeypatch):
    correcta = {"correo": "laura@gimnasio-demo.co", "contrasena": CLAVE}
    monkeypatch.setattr(
        contenedor, "reloj", lambda: RelojFijo(reloj.ahora() + timedelta(minutes=14))
    )
    assert api.post("/api/v1/auth/token", correcta).status_code == 423
    monkeypatch.setattr(
        contenedor, "reloj", lambda: RelojFijo(reloj.ahora() + timedelta(minutes=15))
    )
    assert api.post("/api/v1/auth/token", correcta).status_code == 200


@then("las dos respuestas son iguales")
def iguales(contexto):
    assert contexto["primera"].json() == contexto["segunda"].json()


@then(parsers.parse("{documento} tiene {cantidad:d} pagos guardados"))
def cantidad_pagos(documento, cantidad):
    assert (
        PagoModelo.objects.filter(socio__numero_documento=_documento(documento)[1]).count()
        == cantidad
    )
