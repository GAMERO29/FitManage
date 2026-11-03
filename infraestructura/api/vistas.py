"""Controladores de la API. Cada uno traduce HTTP ↔ caso de uso; ninguno tiene reglas de negocio."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime

from django.conf import settings
from django.core import signing
from django.db import IntegrityError, connection, transaction
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from dominio.calculadora import CalculadoraMembresia
from dominio.modelos import Socio, SolicitudPago, TipoDocumento
from infraestructura import consultas
from infraestructura.api import autenticacion, contenedor, presentacion
from infraestructura.api.http import SolicitudInvalida, leer_json, no_autenticado, problema
from infraestructura.api.seguridad import SOLO_ADMINISTRADOR, TODO_EL_PERSONAL, endpoint
from infraestructura.observabilidad import telemetria
from infraestructura.observabilidad.privacidad import seudonimo
from infraestructura.persistencia.models import IdempotenciaModelo, PlanModelo
from infraestructura.persistencia.repositorios import (
    PagoRepositorioORM,
    PlanRepositorioORM,
    SocioRepositorioORM,
)

COOKIE_RENOVACION = "fm_renovacion"
RUTA_RENOVACION = "/api/v1/auth/renovacion"

registro = logging.getLogger("fitmanage.recepcion")


# --- Sistema -----------------------------------------------------------------------------
@require_GET
@endpoint(roles=None)
def salud(request: HttpRequest) -> JsonResponse:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:  # noqa: BLE001 - cualquier fallo de la base es «no disponible»
        return problema(503, "SERVICIO_NO_DISPONIBLE", "Servicio no disponible")
    ahora = contenedor.reloj().ahora()
    return JsonResponse(
        {
            "estado": "ok",
            "hora": presentacion.fecha_hora(ahora),
            "version": settings.FITMANAGE_VERSION,
        }
    )


# --- Acceso del personal -----------------------------------------------------------------
def _con_cookie(sesion: autenticacion.Sesion) -> JsonResponse:
    respuesta = JsonResponse(
        {"tokenAcceso": sesion.token_acceso, "tipo": "Bearer", "expiraEn": 900, "rol": sesion.rol}
    )
    respuesta.set_cookie(
        COOKIE_RENOVACION,
        sesion.token_renovacion,
        max_age=8 * 3600,
        path=RUTA_RENOVACION,
        secure=True,
        httponly=True,
        samesite="Strict",
    )
    return respuesta


@require_POST
@endpoint(roles=None)
def emitir_token(request: HttpRequest) -> JsonResponse:
    datos = leer_json(request)
    try:
        sesion = autenticacion.iniciar_sesion(
            datos["correo"], datos["contrasena"], contenedor.reloj().ahora()
        )
    except autenticacion.CredencialesInvalidas:
        return problema(401, "CREDENCIALES_INVALIDAS", "Correo o contraseña incorrectos")
    except autenticacion.CuentaBloqueada as bloqueo:
        return problema(
            423,
            "CUENTA_BLOQUEADA",
            "Cuenta bloqueada",
            f"La cuenta se desbloquea a las {bloqueo.hasta.strftime('%H:%M')} "
            "o cuando el administrador la desbloquee.",
            encabezados={"Retry-After": str(bloqueo.segundos)},
        )
    return _con_cookie(sesion)


@require_POST
@endpoint(roles=None)
def renovar_token(request: HttpRequest) -> JsonResponse:
    try:
        sesion = autenticacion.renovar(
            request.COOKIES[COOKIE_RENOVACION], contenedor.reloj().ahora()
        )
    except (KeyError, autenticacion.CredencialesInvalidas):
        return no_autenticado()
    return _con_cookie(sesion)


def _enlace_restablecer(usuario) -> str:
    token = signing.TimestampSigner(salt="fitmanage.restablecer").sign(str(usuario.id))
    return f"{settings.URL_PUBLICA}/restablecer/{token}/"


@require_POST
@endpoint(roles=SOLO_ADMINISTRADOR)
def restablecer_clave(request: HttpRequest, usuarioId: str) -> JsonResponse:  # noqa: N803
    usuario = contenedor.restablecimiento(_enlace_restablecer).restablecer(
        uuid.UUID(usuarioId), solicitante=request.usuario
    )
    return JsonResponse(
        {"enviadoA": presentacion.correo_enmascarado(usuario.correo), "venceEn": 1800},
        status=202,
    )


# --- Socios ------------------------------------------------------------------------------
@require_POST
@endpoint(roles=TODO_EL_PERSONAL)
def registrar_socio(request: HttpRequest) -> JsonResponse:
    datos = leer_json(request)
    ahora = contenedor.reloj().ahora()
    socios = SocioRepositorioORM()
    socio = Socio(
        tipo_documento=TipoDocumento(datos["tipoDocumento"]),
        numero_documento=datos["numeroDocumento"],
        nombres=datos["nombres"].strip(),
        apellidos=datos["apellidos"].strip(),
        telefono=datos["telefono"],
        autorizacion_datos=ahora,
    )
    try:
        with transaction.atomic():
            socios.guardar(socio)
    except IntegrityError:
        return problema(409, "DOCUMENTO_DUPLICADO", "Documento ya registrado")
    respuesta = JsonResponse(presentacion.socio_registrado(socio, ahora), status=201)
    respuesta["Location"] = f"/api/v1/estados/{socio.tipo_documento.value}/{socio.numero_documento}"
    return respuesta


# --- Recepción ---------------------------------------------------------------------------
@require_GET
@endpoint(roles=TODO_EL_PERSONAL)
def consultar_estado(
    request: HttpRequest,
    tipoDocumento: str,  # noqa: N803
    numeroDocumento: str,  # noqa: N803
) -> JsonResponse:
    # Guía 13: el documento nunca entra a la telemetría; solo su seudónimo (ADR N.° 13).
    with telemetria.tracer.start_as_current_span("consultar_estado") as span:
        socio = SocioRepositorioORM().buscar_por_documento(
            TipoDocumento(tipoDocumento), numeroDocumento
        )
        if socio is None:
            resultado, respuesta = (
                "NO_ENCONTRADO",
                problema(404, "NO_ENCONTRADO", "No hay ningún socio con ese documento"),
            )
        else:
            hoy = contenedor.reloj().hoy()
            pagos = PagoRepositorioORM().vigentes_de(socio)
            estado, vence = CalculadoraMembresia().estado_de(pagos, hoy)
            resultado = estado.value
            respuesta = JsonResponse(presentacion.estado_publico(socio, estado, vence, hoy))
        huella = seudonimo(tipoDocumento, numeroDocumento)
        span.set_attributes(
            {
                "fitmanage.documento.tipo": tipoDocumento,
                "fitmanage.socio.seudonimo": huella,
                "fitmanage.resultado": resultado,
            }
        )
        telemetria.consultas_estado.add(1, {"resultado": resultado})
        registro.info(
            "consulta de estado",
            extra={
                "evento": "consulta_estado",
                "tipo_documento": tipoDocumento,
                "seudonimo": huella,
                "resultado": resultado,
            },
        )
    return respuesta


@require_GET
@endpoint(roles=TODO_EL_PERSONAL)
def listar_estados(request: HttpRequest) -> JsonResponse:
    desde = request.GET.get("cambiadosDesde")
    cambiados = datetime.fromisoformat(desde) if desde else None
    ahora = contenedor.reloj().ahora()
    filas = consultas.estados(ahora.date(), cambiados)
    return JsonResponse(
        {
            "generadoEl": presentacion.fecha_hora(ahora),
            "estados": [presentacion.estado_publico(s, e, v, ahora.date()) for s, e, v in filas],
        }
    )


# --- Membresías y cobros -----------------------------------------------------------------
@require_GET
@endpoint(roles=TODO_EL_PERSONAL)
def listar_planes(request: HttpRequest) -> JsonResponse:
    planes = PlanModelo.objects.filter(activo=True).order_by("duracion_dias")
    return JsonResponse(
        [
            {
                "id": str(p.id),
                "nombre": p.nombre,
                "duracionDias": p.duracion_dias,
                "precio": int(p.precio),
            }
            for p in planes
        ],
        safe=False,
    )


def _nombre_plan(plan_id: uuid.UUID) -> str:
    return PlanRepositorioORM().obtener(plan_id).nombre


def _respuesta_guardada(clave: uuid.UUID) -> JsonResponse:
    previa = IdempotenciaModelo.objects.get(clave=clave)
    respuesta = JsonResponse(previa.cuerpo, status=previa.estado_http)
    respuesta["Location"] = f"/api/v1/pagos/{previa.cuerpo['id']}"
    respuesta["Idempotent-Replayed"] = "true"
    return respuesta


@require_POST
@endpoint(roles=TODO_EL_PERSONAL)
def registrar_pago(request: HttpRequest) -> JsonResponse:
    clave = uuid.UUID(request.headers["Idempotency-Key"])
    datos = leer_json(request)
    solicitud = SolicitudPago(
        tipo_documento=TipoDocumento(datos["tipoDocumento"]),
        numero_documento=datos["numeroDocumento"],
        plan_id=uuid.UUID(datos["planId"]),
        medio=datos["medio"],
        referencia=datos.get("referencia"),
    )
    with transaction.atomic():
        try:
            with transaction.atomic():
                registro = IdempotenciaModelo.objects.create(
                    clave=clave, usuario_id=request.usuario.id
                )
        except IntegrityError:
            return _respuesta_guardada(clave)
        pago = contenedor.registro_pago().registrar_pago(solicitud, request.usuario)
        cuerpo = presentacion.pago(pago, _nombre_plan(pago.plan_id))
        registro.estado_http, registro.cuerpo = 201, cuerpo
        registro.save(update_fields=["estado_http", "cuerpo"])
    respuesta = JsonResponse(cuerpo, status=201)
    respuesta["Location"] = f"/api/v1/pagos/{pago.id}"
    return respuesta


@require_http_methods(["PATCH"])
@endpoint(roles=SOLO_ADMINISTRADOR)
def anular_pago(request: HttpRequest, pagoId: str) -> JsonResponse:  # noqa: N803
    datos = leer_json(request)
    with transaction.atomic():
        pago = contenedor.anulacion_pago().anular(
            uuid.UUID(pagoId), request.usuario, datos["motivo"]
        )
    return JsonResponse(presentacion.pago(pago, _nombre_plan(pago.plan_id)))


# --- Reportes y recordatorios ------------------------------------------------------------
@require_GET
@endpoint(roles=SOLO_ADMINISTRADOR)
def reporte_ingresos(request: HttpRequest) -> JsonResponse:
    desde = date.fromisoformat(request.GET["desde"])
    hasta = date.fromisoformat(request.GET["hasta"])
    if hasta < desde or (hasta - desde).days > 366:
        raise SolicitudInvalida(
            [
                {
                    "campo": "hasta",
                    "mensaje": "Debe ser igual o posterior a desde y máximo 366 días después.",
                }
            ]
        )
    return JsonResponse(consultas.reporte_ingresos(desde, hasta))


@require_GET
@endpoint(roles=TODO_EL_PERSONAL)
def listar_vencimientos(request: HttpRequest) -> JsonResponse:
    dias = int(request.GET.get("dias", "3"))
    nombres = {p.id: p.nombre for p in PlanModelo.objects.all()}
    filas = consultas.vencimientos(contenedor.reloj().hoy(), dias, nombres)
    return JsonResponse(filas, safe=False)
