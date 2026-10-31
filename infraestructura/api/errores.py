"""Traducción de los errores del dominio a códigos HTTP del contrato (Nivel 2 de Richardson)."""

from __future__ import annotations

from django.http import JsonResponse

from dominio import errores as e
from infraestructura.api.http import problema

TABLA: dict[type[e.ErrorDeDominio], tuple[int, str, str]] = {
    e.DatosInvalidos: (400, "SOLICITUD_INVALIDA", "Solicitud inválida"),
    e.ReferenciaRequerida: (400, "SOLICITUD_INVALIDA", "Falta la referencia del comprobante"),
    e.MedioPagoInvalido: (400, "SOLICITUD_INVALIDA", "Medio de pago no aceptado"),
    e.MotivoRequerido: (400, "SOLICITUD_INVALIDA", "Indique el motivo de la anulación"),
    e.PermisoDenegado: (403, "SIN_PERMISO", "Su rol no puede hacer esto"),
    e.SocioNoEncontrado: (404, "NO_ENCONTRADO", "No hay ningún socio con ese documento"),
    e.PlanNoDisponible: (404, "NO_ENCONTRADO", "El plan no existe o está desactivado"),
    e.PagoNoEncontrado: (404, "NO_ENCONTRADO", "El pago no existe"),
    e.UsuarioNoEncontrado: (404, "NO_ENCONTRADO", "La cuenta no existe"),
    e.ReferenciaDuplicada: (409, "COMPROBANTE_DUPLICADO", "Comprobante duplicado"),
    e.PagoNoAnulable: (409, "NO_ES_EL_ULTIMO_PAGO", "Solo se puede anular el último pago vigente"),
    e.CorreoNoDisponible: (503, "CORREO_NO_DISPONIBLE", "No se pudo enviar el correo"),
}


def respuesta_de_error(error: e.ErrorDeDominio) -> JsonResponse:
    for tipo in type(error).__mro__:
        if tipo in TABLA:
            status, codigo, titulo = TABLA[tipo]
            return problema(status, codigo, titulo, detalle=str(error) or None)
    return problema(400, "SOLICITUD_INVALIDA", "Solicitud inválida", detalle=str(error))
