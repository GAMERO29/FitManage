"""Raíz de composición de la API: aquí, y solo aquí, se eligen los adaptadores reales.

Las pruebas reemplazan `reloj` y `correo` (las fronteras con el exterior); nunca el dominio.
"""

from __future__ import annotations

from aplicacion.acceso import RestablecimientoClaveService
from aplicacion.pagos import AnulacionPagoService, RegistroPagoService
from aplicacion.planes import GestionPlanesService
from aplicacion.socios import ConsultaEstadoService, RegistroSocioService
from dominio.puertos import CorreoSaliente, Reloj
from infraestructura.correo import CorreoDjango
from infraestructura.persistencia.repositorios import (
    PagoRepositorioORM,
    PlanRepositorioORM,
    SocioRepositorioORM,
    UsuarioRepositorioORM,
)
from infraestructura.reloj import RelojBogota


def reloj() -> Reloj:
    return RelojBogota()


def correo() -> CorreoSaliente:
    return CorreoDjango()


def registro_pago() -> RegistroPagoService:
    return RegistroPagoService(
        SocioRepositorioORM(), PlanRepositorioORM(), PagoRepositorioORM(), reloj()
    )


def registro_socio() -> RegistroSocioService:
    return RegistroSocioService(SocioRepositorioORM(), reloj())


def consulta_estado() -> ConsultaEstadoService:
    return ConsultaEstadoService(SocioRepositorioORM(), PagoRepositorioORM(), reloj())


def nombre_plan(plan_id) -> str:
    return PlanRepositorioORM().obtener(plan_id).nombre


def anulacion_pago() -> AnulacionPagoService:
    return AnulacionPagoService(PagoRepositorioORM(), reloj())


def restablecimiento(enlace_para) -> RestablecimientoClaveService:
    return RestablecimientoClaveService(UsuarioRepositorioORM(), correo(), enlace_para)


def gestion_planes() -> GestionPlanesService:
    return GestionPlanesService(PlanRepositorioORM())
