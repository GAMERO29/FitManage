"""Errores del negocio de FitManage.

Cada error nombra la regla de negocio que protege, para que la capa de
presentación pueda mostrar un mensaje claro sin conocer los detalles.
"""


class ErrorDeDominio(Exception):
    """Base de todos los errores de reglas de negocio."""


class DatosInvalidos(ErrorDeDominio):
    """Un dato no cumple las invariantes de la entidad."""


class SocioNoEncontrado(ErrorDeDominio):
    """No existe un socio con el tipo y número de documento indicados."""


class PlanNoDisponible(ErrorDeDominio):
    """El plan no existe o está desactivado (RN-09)."""


class MedioPagoInvalido(ErrorDeDominio):
    """El medio de pago no pertenece a los medios aceptados por el gimnasio."""


class ReferenciaRequerida(ErrorDeDominio):
    """Un pago por medio digital no trae la referencia del comprobante (RN-06)."""


class ReferenciaDuplicada(ErrorDeDominio):
    """La referencia ya pertenece a otro pago vigente (RN-06)."""


class PermisoDenegado(ErrorDeDominio):
    """El usuario no tiene el rol necesario para la acción (RN-07, RNF-05)."""


class PagoNoAnulable(ErrorDeDominio):
    """El pago ya fue anulado o no es el último pago vigente del socio (RN-07)."""


class MotivoRequerido(ErrorDeDominio):
    """La anulación exige un motivo escrito (RN-07)."""


class PagoNoEncontrado(ErrorDeDominio):
    """No existe un pago con ese identificador."""


class UsuarioNoEncontrado(ErrorDeDominio):
    """No existe una cuenta del personal con ese identificador."""


class CorreoNoDisponible(ErrorDeDominio):
    """El servidor de correo no aceptó el mensaje; nada del negocio cambió."""
