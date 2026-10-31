"""Respuestas JSON y errores `application/problem+json` (RFC 9457) del contrato."""

from __future__ import annotations

import json

from django.http import HttpRequest, JsonResponse

ERRORES = "https://github.com/GAMERO29/FitManage/blob/main/docs/api/errores.md#"


class SolicitudInvalida(Exception):
    def __init__(self, errores: list[dict]) -> None:
        super().__init__("Solicitud inválida")
        self.errores = errores


def problema(
    status: int,
    codigo: str,
    titulo: str,
    detalle: str | None = None,
    errores: list[dict] | None = None,
    encabezados: dict[str, str] | None = None,
) -> JsonResponse:
    cuerpo: dict = {
        "type": ERRORES + codigo.lower().replace("_", "-"),
        "title": titulo,
        "status": status,
        "codigo": codigo,
    }
    if detalle:
        cuerpo["detail"] = detalle
    if errores:
        cuerpo["errores"] = errores
    respuesta = JsonResponse(cuerpo, status=status, content_type="application/problem+json")
    for nombre, valor in (encabezados or {}).items():
        respuesta[nombre] = valor
    return respuesta


def no_autenticado(detalle: str | None = None) -> JsonResponse:
    return problema(
        401,
        "NO_AUTENTICADO",
        "Inicie sesión de nuevo",
        detalle,
        encabezados={"WWW-Authenticate": 'Bearer realm="fitmanage-api"'},
    )


def leer_json(request: HttpRequest) -> dict:
    """El contrato ya validó el cuerpo; aquí solo se decodifica."""
    return json.loads(request.body or b"{}")
