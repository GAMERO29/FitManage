"""Software III · Guía 12: la anulación de pagos escrita como Transaction Script.

Un procedimiento por operación, sobre filas (diccionarios), como quedaría si cada vista hiciera
todo. Se escribió a propósito sin helpers compartidos entre procedimientos: así se ve dónde se
repite cada regla. Extraer esos helpers sería el primer paso hacia un Domain Model.
Solo existe para el experimento; FitManage no lo usa.
"""

from __future__ import annotations

from datetime import datetime

from dominio.errores import MotivoRequerido, PagoNoAnulable, PagoNoEncontrado, PermisoDenegado

ZONA = "America/Bogota"


def anular_ultimo(filas: list[dict], socio_id, usuario: dict, motivo: str, ahora: datetime) -> dict:
    """Botón «Anular último pago» del historial."""
    if not usuario["activo"] or usuario["rol"] not in ("ADMINISTRADOR", "RECEPCIONISTA"):
        raise PermisoDenegado("Su rol no puede anular pagos ni cambiar planes.")
    vigentes = [f for f in filas if f["socio_id"] == socio_id and f["estado"] == "VIGENTE"]
    if not vigentes:
        raise PagoNoAnulable("El socio no tiene pagos vigentes.")
    fila = max(vigentes, key=lambda f: (f["inicia"], f["registrado_en"]))
    if usuario["rol"] != "ADMINISTRADOR" and (
        fila["registrado_por_id"] != usuario["id"] or fila["registrado_en"].date() != ahora.date()
    ):
        raise PermisoDenegado("Solo puede anular los pagos que usted registró hoy.")
    if len((motivo or "").strip()) < 5:  # regla del motivo, copia 1 de 3 (CR-02)
        raise MotivoRequerido("Explique el motivo con al menos 5 caracteres.")
    fila.update(
        estado="ANULADO", motivo=motivo.strip(), anulado_por_id=usuario["id"], anulado_en=ahora
    )
    return fila


def anular_por_id(filas: list[dict], pago_id, usuario: dict, motivo: str, ahora: datetime) -> dict:
    """`PATCH /pagos/{pagoId}`."""
    if not usuario["activo"] or usuario["rol"] not in ("ADMINISTRADOR", "RECEPCIONISTA"):
        raise PermisoDenegado("Su rol no puede anular pagos ni cambiar planes.")
    fila = next((f for f in filas if f["id"] == pago_id), None)
    if fila is None:
        raise PagoNoEncontrado(f"No existe el pago {pago_id}.")
    if fila["estado"] != "VIGENTE":
        raise PagoNoAnulable("El pago ya está anulado.")
    vigentes = [f for f in filas if f["socio_id"] == fila["socio_id"] and f["estado"] == "VIGENTE"]
    if max(vigentes, key=lambda f: (f["inicia"], f["registrado_en"]))["id"] != pago_id:
        raise PagoNoAnulable("Solo se puede anular el último pago vigente del socio.")
    if usuario["rol"] != "ADMINISTRADOR" and (
        fila["registrado_por_id"] != usuario["id"] or fila["registrado_en"].date() != ahora.date()
    ):
        raise PermisoDenegado("Solo puede anular los pagos que usted registró hoy.")
    if len((motivo or "").strip()) < 5:  # regla del motivo, copia 2 de 3 (CR-02)
        raise MotivoRequerido("Explique el motivo con al menos 5 caracteres.")
    fila.update(
        estado="ANULADO", motivo=motivo.strip(), anulado_por_id=usuario["id"], anulado_en=ahora
    )
    return fila


def anular_para_cambio_de_plan(
    filas: list[dict], pago_id, usuario: dict, motivo: str, ahora: datetime
) -> dict:
    """Primera mitad del cambio de plan: sin el límite del día para la recepcionista (ADR 18)."""
    if not usuario["activo"] or usuario["rol"] not in ("ADMINISTRADOR", "RECEPCIONISTA"):
        raise PermisoDenegado("Su rol no puede anular pagos ni cambiar planes.")
    fila = next((f for f in filas if f["id"] == pago_id), None)
    if fila is None:
        raise PagoNoEncontrado(f"No existe el pago {pago_id}.")
    if fila["estado"] != "VIGENTE":
        raise PagoNoAnulable("El pago ya está anulado.")
    vigentes = [f for f in filas if f["socio_id"] == fila["socio_id"] and f["estado"] == "VIGENTE"]
    if max(vigentes, key=lambda f: (f["inicia"], f["registrado_en"]))["id"] != pago_id:
        raise PagoNoAnulable("Solo se puede anular el último pago vigente del socio.")
    if len((motivo or "").strip()) < 5:  # regla del motivo, copia 3 de 3 (CR-02)
        raise MotivoRequerido("Explique el motivo con al menos 5 caracteres.")
    fila.update(
        estado="ANULADO", motivo=motivo.strip(), anulado_por_id=usuario["id"], anulado_en=ahora
    )
    return fila
