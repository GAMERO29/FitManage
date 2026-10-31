"""Fixtures compartidas por las pruebas de integración y de aceptación de la API.

Regla de oro de la Guía 7: todo corre contra la base de pruebas efímera que crea pytest-django
(SQLite en memoria en local, `test_fitmanage` dentro del contenedor de PostgreSQL de CI).
Solo se reemplazan las fronteras con el exterior: el reloj y el servidor de correo.
"""

from __future__ import annotations

import json
import uuid
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.hashers import make_password
from dobles import RelojFijo
from fechas import bogota
from openapi_core.contrib.django import DjangoOpenAPIRequest, DjangoOpenAPIResponse

from dominio.modelos import MedioPago, Pago, Plan, Rol, Socio, TipoDocumento, Usuario
from infraestructura.api import contenedor, contrato
from infraestructura.persistencia.models import UsuarioModelo
from infraestructura.persistencia.repositorios import (
    PagoRepositorioORM,
    PlanRepositorioORM,
    SocioRepositorioORM,
)

AHORA = bogota(2026, 10, 7, 18, 45)
CLAVE = "demo2026"
ID_MENSUAL = uuid.UUID("7a5e1b2c-9d40-4c8f-b6a3-2e1f0d9c8b22")
ID_PAGO_JORGE = uuid.UUID("5e2d8c1a-0b7f-4a93-9c64-1f3e7a2b8d44")


@pytest.fixture(autouse=True)
def hasher_rapido(settings):
    """MD5 solo en pruebas: el hash real (PBKDF2) haría la suite 50 veces más lenta."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def reloj(monkeypatch):
    """Frontera 1: la hora. Se fija el miércoles 7 de octubre de 2026 a las 6:45 p. m."""
    fijo = RelojFijo(AHORA)
    monkeypatch.setattr(contenedor, "reloj", lambda: fijo)
    return fijo


def _cuenta(nombre: str, correo: str, rol: Rol) -> Usuario:
    usuario = Usuario(nombre, correo, rol)
    UsuarioModelo.objects.create(
        id=usuario.id,
        nombre=nombre,
        correo=correo,
        rol=rol.value,
        clave_hash=make_password(CLAVE),
    )
    return usuario


def sembrar() -> dict:
    """Los datos de demostración del prototipo, guardados con los repositorios reales."""
    laura = _cuenta("Laura", "laura@gimnasio-demo.co", Rol.RECEPCIONISTA)
    carlos = _cuenta("Carlos", "carlos@gimnasio-demo.co", Rol.ADMINISTRADOR)
    diego = _cuenta("Diego Salcedo", "diego@gimnasio-demo.co", Rol.ENTRENADOR)
    planes = PlanRepositorioORM()
    mensual = Plan("Mensual", 30, Decimal("75000"), id=ID_MENSUAL)
    trimestral = Plan("Trimestral", 90, Decimal("200000"))
    diario = Plan("Diario", 1, Decimal("8000"))
    for plan in (mensual, trimestral, diario):
        planes.guardar(plan)
    autorizacion = bogota(2026, 5, 25, 9, 14)
    socios = SocioRepositorioORM()
    ana = Socio(TipoDocumento.CC, "1090123456", "Ana", "Pérez", "3000000005", autorizacion)
    jorge = Socio(TipoDocumento.CC, "1093445566", "Jorge", "Rincón", "3000000006", autorizacion)
    maria = Socio(
        TipoDocumento.PPT, "25789456", "María Fernanda", "Gil", "3000000004", autorizacion
    )
    for socio in (ana, jorge, maria):
        socios.guardar(socio)
    pagos = PagoRepositorioORM()
    pagos.guardar(
        _pago(ana, mensual, date(2026, 9, 22), date(2026, 10, 21), laura, MedioPago.EFECTIVO, None)
    )
    pagos.guardar(
        _pago(
            jorge,
            mensual,
            date(2026, 8, 31),
            date(2026, 9, 29),
            laura,
            MedioPago.NEQUI,
            "M123456",
            ID_PAGO_JORGE,
        )
    )
    return {
        "laura": laura,
        "carlos": carlos,
        "diego": diego,
        "mensual": mensual,
        "trimestral": trimestral,
        "diario": diario,
        "ana": ana,
        "jorge": jorge,
        "maria": maria,
    }


@pytest.fixture
def gimnasio(db, reloj):
    return sembrar()


def _pago(socio, plan, inicio, vence, usuario, medio, referencia, id_=None) -> Pago:
    extra = {"id": id_} if id_ else {}
    return Pago(
        socio=socio,
        plan_id=plan.id,
        valor=plan.precio,
        duracion_dias=plan.duracion_dias,
        medio=medio,
        referencia=referencia,
        fecha_inicio=inicio,
        fecha_vencimiento=vence,
        registrado_por=usuario,
        registrado_en=bogota(inicio.year, inicio.month, inicio.day, 18, 0),
        **extra,
    )


class ClienteAPI:
    """Cliente HTTP que además valida CADA respuesta contra docs/api/openapi.yaml.

    Si un controlador devuelve un campo, un código o un tipo que el contrato no promete,
    la prueba falla aunque el caso de negocio parezca correcto.
    """

    def __init__(self, client) -> None:
        self._client = client
        self.token: str | None = None

    def como(self, correo: str) -> ClienteAPI:
        respuesta = self.post("/api/v1/auth/token", {"correo": correo, "contrasena": CLAVE})
        assert respuesta.status_code == 200, respuesta.content
        self.token = respuesta.json()["tokenAcceso"]
        return self

    def _encabezados(self, extra: dict | None) -> dict:
        encabezados = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"} if self.token else {}
        for nombre, valor in (extra or {}).items():
            encabezados["HTTP_" + nombre.upper().replace("-", "_")] = valor
        return encabezados

    def _validar(self, respuesta):
        contrato.especificacion().validate_response(
            DjangoOpenAPIRequest(respuesta.wsgi_request), DjangoOpenAPIResponse(respuesta)
        )
        return respuesta

    def get(self, ruta: str, datos: dict | None = None, encabezados: dict | None = None):
        return self._validar(self._client.get(ruta, datos or {}, **self._encabezados(encabezados)))

    def post(self, ruta: str, cuerpo: dict | None = None, encabezados: dict | None = None):
        return self._validar(
            self._client.post(
                ruta, json.dumps(cuerpo or {}), "application/json", **self._encabezados(encabezados)
            )
        )

    def patch(self, ruta: str, cuerpo: dict, encabezados: dict | None = None):
        return self._validar(
            self._client.patch(
                ruta, json.dumps(cuerpo), "application/json", **self._encabezados(encabezados)
            )
        )


@pytest.fixture
def api(client, gimnasio):
    return ClienteAPI(client)
