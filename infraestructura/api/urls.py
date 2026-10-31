"""Los nombres de los parámetros son los del contrato: openapi-core los usa para validar."""

from django.urls import path

from infraestructura.api import vistas

urlpatterns = [
    path("salud", vistas.salud),
    path("auth/token", vistas.emitir_token),
    path("auth/renovacion", vistas.renovar_token),
    path("personal/<str:usuarioId>/restablecimiento", vistas.restablecer_clave),
    path("socios", vistas.registrar_socio),
    path("estados", vistas.listar_estados),
    path("estados/<str:tipoDocumento>/<str:numeroDocumento>", vistas.consultar_estado),
    path("planes", vistas.listar_planes),
    path("pagos", vistas.registrar_pago),
    path("pagos/<str:pagoId>", vistas.anular_pago),
    path("reportes/ingresos", vistas.reporte_ingresos),
    path("vencimientos", vistas.listar_vencimientos),
]
