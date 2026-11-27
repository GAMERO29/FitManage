"""Traducción de filas del ORM a objetos del dominio, publicada para los demás adaptadores.

Antes eran funciones privadas de repositorios.py que autenticacion.py y consultas.py importaban
igual (Software III, Guía 07). Una función pública dice que otros cuentan con ella; un cambio
aquí se revisa con las pruebas de los tres consumidores.
"""

from __future__ import annotations

from dominio.modelos import (
    ZONA_HORARIA,
    EstadoPago,
    MedioPago,
    Pago,
    Rol,
    Socio,
    TipoDocumento,
    Usuario,
)
from infraestructura.persistencia.models import PagoModelo, SocioModelo, UsuarioModelo


def a_socio(m: SocioModelo) -> Socio:
    return Socio(
        tipo_documento=TipoDocumento(m.tipo_documento),
        numero_documento=m.numero_documento,
        nombres=m.nombres,
        apellidos=m.apellidos,
        telefono=m.telefono,
        autorizacion_datos=m.autorizacion_datos.astimezone(ZONA_HORARIA),
        id=m.id,
    )


def a_usuario(m: UsuarioModelo) -> Usuario:
    return Usuario(nombre=m.nombre, correo=m.correo, rol=Rol(m.rol), activo=m.activo, id=m.id)


def a_pago(m: PagoModelo) -> Pago:
    return Pago(
        socio=a_socio(m.socio),
        plan_id=m.plan_id,
        valor=m.valor,
        duracion_dias=m.duracion_dias,
        medio=MedioPago(m.medio),
        referencia=m.referencia,
        fecha_inicio=m.fecha_inicio,
        fecha_vencimiento=m.fecha_vencimiento,
        registrado_por=a_usuario(m.registrado_por),
        registrado_en=m.registrado_en.astimezone(ZONA_HORARIA),
        estado=EstadoPago(m.estado),
        fecha_anulacion=m.fecha_anulacion.astimezone(ZONA_HORARIA) if m.fecha_anulacion else None,
        anulado_por=a_usuario(m.anulado_por) if m.anulado_por else None,
        motivo_anulacion=m.motivo_anulacion,
        id=m.id,
    )
