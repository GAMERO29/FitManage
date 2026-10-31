"""Modelos de lectura de Recepción, Reportes y Recordatorios (FPI-21: solo leen, nunca escriben).

El estado se calcula siempre con `CalculadoraMembresia` del dominio; aquí solo se consulta.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from urllib.parse import quote
from uuid import UUID

from dominio.calculadora import CalculadoraMembresia
from dominio.modelos import ZONA_HORARIA, EstadoMembresia, EstadoPago, MedioPago, Pago, Socio
from infraestructura.persistencia.models import PagoModelo, SocioModelo
from infraestructura.persistencia.repositorios import _a_pago, _a_socio

CALCULADORA = CalculadoraMembresia()


def _vigentes_por_socio() -> dict:
    pagos = PagoModelo.objects.select_related("socio", "registrado_por", "anulado_por").filter(
        estado=EstadoPago.VIGENTE.value
    )
    agrupados: dict = defaultdict(list)
    for m in pagos:
        agrupados[m.socio_id].append(_a_pago(m))
    return agrupados


def estados(
    hoy: date, cambiados_desde: datetime | None = None
) -> list[tuple[Socio, EstadoMembresia, date | None]]:
    """Todos los socios con su estado.

    Con `cambiados_desde`, solo los que tuvieron pagos o anulaciones después de esa hora.
    """
    socios = SocioModelo.objects.all()
    if cambiados_desde is not None:
        socios = socios.filter(pagos__registrado_en__gte=cambiados_desde) | socios.filter(
            pagos__fecha_anulacion__gte=cambiados_desde
        )
    vigentes = _vigentes_por_socio()
    filas = []
    for m in socios.distinct().order_by("apellidos", "nombres"):
        estado, vence = CALCULADORA.estado_de(vigentes.get(m.id, []), hoy)
        filas.append((_a_socio(m), estado, vence))
    return filas


def _inicio_del_dia(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=ZONA_HORARIA)


def reporte_ingresos(desde: date, hasta: date) -> dict:
    """RF-05: pagos registrados en el periodo (hora de Colombia); los anulados no suman."""
    pagos = PagoModelo.objects.filter(
        registrado_en__gte=_inicio_del_dia(desde),
        registrado_en__lt=_inicio_del_dia(hasta + timedelta(days=1)),
    )
    por_medio = {medio: {"medio": medio.value, "pagos": 0, "total": 0} for medio in MedioPago}
    anulados = 0
    for m in pagos:
        if m.estado != EstadoPago.VIGENTE.value:
            anulados += 1
            continue
        fila = por_medio[MedioPago(m.medio)]
        fila["pagos"] += 1
        fila["total"] += int(m.valor)
    filas = list(por_medio.values())
    return {
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        "total": sum(f["total"] for f in filas),
        "pagos": sum(f["pagos"] for f in filas),
        "anulados": anulados,
        "porMedio": filas,
    }


def _enlace_whatsapp(socio: Socio, vence: date) -> str:
    texto = (
        f"Hola {socio.nombres.split()[0]}, te recordamos que tu membresía en el gimnasio "
        f"vence el {vence.strftime('%d/%m/%Y')}. Te esperamos para renovarla."
    )
    return f"https://wa.me/57{socio.telefono}?text={quote(texto)}"


def _plan_del_ultimo(pagos: list[Pago]) -> UUID:
    return max(pagos, key=lambda p: p.fecha_vencimiento).plan_id


def vencimientos(hoy: date, dias: int, nombres_de_plan: dict[UUID, str]) -> list[dict]:
    """RF-05/RF-06: socios cuyo vencimiento actual cae entre hoy y hoy + `dias`."""
    filas = []
    limite = hoy + timedelta(days=dias)
    for pagos in _vigentes_por_socio().values():
        estado, vence = CALCULADORA.estado_de(pagos, hoy)
        if estado is not EstadoMembresia.ACTIVO or vence > limite:
            continue
        socio = pagos[0].socio
        filas.append(
            {
                "nombreCorto": f"{socio.nombres.split()[0]} {socio.apellidos[:1]}.",
                "plan": nombres_de_plan.get(_plan_del_ultimo(pagos), "Plan"),
                "venceEl": vence.isoformat(),
                "telefono": socio.telefono,
                "enlaceWhatsApp": _enlace_whatsapp(socio, vence),
            }
        )
    return sorted(filas, key=lambda f: (f["venceEl"], f["nombreCorto"]))
