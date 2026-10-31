"""Esquemas de respuesta del contrato. Aquí se aplica el mínimo privilegio (Ley 1581 de 2012)."""

from __future__ import annotations

from datetime import date, datetime

from django.utils.crypto import salted_hmac

from dominio.modelos import EstadoMembresia, Pago, Socio, TipoDocumento


def nombre_corto(nombres: str, apellidos: str) -> str:
    """«Ana Pérez» → «Ana P.»: suficiente para que la recepcionista confirme a quién atiende."""
    primer_nombre = nombres.split()[0]
    inicial = apellidos.strip()[:1].upper()
    return f"{primer_nombre} {inicial}." if inicial else primer_nombre


def documento_enmascarado(tipo: TipoDocumento, numero: str) -> str:
    return f"{tipo.value} {'*' * (len(numero) - 4)}{numero[-4:]}"


def correo_enmascarado(correo: str) -> str:
    usuario, _, dominio = correo.partition("@")
    return f"{usuario[:1]}{'*' * max(len(usuario) - 1, 1)}@{dominio}"


def huella_documento(tipo: TipoDocumento, numero: str) -> str:
    """HMAC truncado: la caché del celular busca por documento sin guardar el número."""
    return salted_hmac(
        "fitmanage.estado", f"{tipo.value}:{numero}", algorithm="sha256"
    ).hexdigest()[:16]


def fecha_hora(momento: datetime) -> str:
    return momento.isoformat(timespec="seconds")


def estado_publico(socio: Socio, estado: EstadoMembresia, vence: date | None, hoy: date) -> dict:
    cuerpo: dict = {
        "documentoHash": huella_documento(socio.tipo_documento, socio.numero_documento),
        "nombreCorto": nombre_corto(socio.nombres, socio.apellidos),
        "documentoEnmascarado": documento_enmascarado(socio.tipo_documento, socio.numero_documento),
        "estado": estado.value,
    }
    if vence is not None:
        cuerpo["venceEl"] = vence.isoformat()
    if estado is EstadoMembresia.ACTIVO:
        cuerpo["diasRestantes"] = (vence - hoy).days + 1
    elif estado is EstadoMembresia.VENCIDO:
        cuerpo["diasMora"] = (hoy - vence).days
    return cuerpo


def socio_registrado(socio: Socio, registrado_el: datetime) -> dict:
    return {
        "id": str(socio.id),
        "nombreCorto": f"{socio.nombres} {socio.apellidos.strip()[:1].upper()}.",
        "documentoEnmascarado": documento_enmascarado(socio.tipo_documento, socio.numero_documento),
        "estado": EstadoMembresia.SIN_MEMBRESIA.value,
        "registradoEl": fecha_hora(registrado_el),
    }


def pago(p: Pago, nombre_plan: str) -> dict:
    cuerpo: dict = {
        "id": str(p.id),
        "plan": nombre_plan,
        "medio": p.medio.value,
        "valor": int(p.valor),
        "inicia": p.fecha_inicio.isoformat(),
        "vence": p.fecha_vencimiento.isoformat(),
        "estado": p.estado.value,
        "registradoPor": p.registrado_por.nombre,
        "registradoEl": fecha_hora(p.registrado_en),
    }
    if p.referencia:
        cuerpo["referencia"] = p.referencia
    if p.fecha_anulacion is not None:
        cuerpo["anulacion"] = {
            "motivo": p.motivo_anulacion,
            "anuladoPor": p.anulado_por.nombre,
            "anuladoEl": fecha_hora(p.fecha_anulacion),
        }
    return cuerpo
