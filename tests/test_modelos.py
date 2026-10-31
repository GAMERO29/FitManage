from datetime import date
from decimal import Decimal

import pytest
from fechas import bogota

from dominio.errores import DatosInvalidos, MotivoRequerido, PagoNoAnulable
from dominio.modelos import (
    EstadoPago,
    MedioPago,
    NumeroDocumento,
    Plan,
    Rol,
    Socio,
    Telefono,
    TipoDocumento,
    Usuario,
)


@pytest.mark.parametrize(
    ("medio", "esperado"),
    [
        (MedioPago.EFECTIVO, False),
        (MedioPago.NEQUI, True),
        (MedioPago.DAVIPLATA, True),
        (MedioPago.TRANSFERENCIA, True),
    ],
)
def test_solo_el_efectivo_no_requiere_referencia(medio, esperado):
    assert medio.requiere_referencia() is esperado


def test_socio_sin_autorizacion_de_datos_no_se_crea():
    with pytest.raises(DatosInvalidos):
        Socio(TipoDocumento.CC, "1090000001", "Pedro", "Ríos", "3000000009", None)


def test_socio_con_ppt_se_registra():
    socio = Socio(
        TipoDocumento.PPT,
        "25789456",
        "María",
        "Gil",
        "3000000004",
        bogota(2026, 1, 1),
    )
    assert socio.tipo_documento is TipoDocumento.PPT


@pytest.mark.parametrize(("duracion", "precio"), [(0, Decimal("1000")), (30, Decimal("0"))])
def test_plan_con_duracion_o_precio_no_positivo_se_rechaza(duracion, precio):
    with pytest.raises(DatosInvalidos):
        Plan("Inválido", duracion, precio)


def test_solo_un_administrador_activo_es_administrador():
    assert Usuario("A", "a@x.test", Rol.ADMINISTRADOR).es_administrador()
    assert not Usuario("B", "b@x.test", Rol.ADMINISTRADOR, activo=False).es_administrador()
    assert not Usuario("C", "c@x.test", Rol.RECEPCIONISTA).es_administrador()


def test_pago_con_vencimiento_anterior_al_inicio_se_rechaza(ana, mensual, laura, fabrica_pago):
    with pytest.raises(DatosInvalidos):
        fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 10, 6), laura)


def test_anular_pago_lo_deja_anulado_con_motivo_y_responsable(
    ana, mensual, laura, carlos, fabrica_pago
):
    pago = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    ahora = bogota(2026, 10, 7, 19, 0)
    pago.anular("  Plan equivocado ", carlos, ahora)
    assert pago.estado is EstadoPago.ANULADO
    assert pago.motivo_anulacion == "Plan equivocado"
    assert pago.anulado_por == carlos and pago.fecha_anulacion == ahora
    assert not pago.esta_vigente()


def test_un_pago_no_se_anula_dos_veces(ana, mensual, laura, carlos, fabrica_pago):
    pago = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    pago.anular("Error", carlos, bogota(2026, 10, 7, 19, 0))
    with pytest.raises(PagoNoAnulable):
        pago.anular("Otra vez", carlos, bogota(2026, 10, 7, 19, 5))


def test_anular_sin_motivo_se_rechaza(ana, mensual, laura, carlos, fabrica_pago):
    pago = fabrica_pago(ana, mensual, date(2026, 10, 7), date(2026, 11, 5), laura)
    with pytest.raises(MotivoRequerido):
        pago.anular("   ", carlos, bogota(2026, 10, 7, 19, 0))


def test_socio_sin_numero_de_documento_no_se_crea():
    with pytest.raises(DatosInvalidos):
        Socio(TipoDocumento.CC, "  ", "Pedro", "Ríos", "3000000009", bogota(2026, 1, 1))


@pytest.mark.parametrize("telefono", ["300000000", "30000000001", "300-000-000", "30000000ab"])
def test_telefono_debe_tener_diez_digitos(telefono):
    with pytest.raises(DatosInvalidos):
        Telefono(telefono)


@pytest.mark.parametrize(
    ("tipo", "numero", "valido"),
    [
        (TipoDocumento.CC, "1090123456", True),
        (TipoDocumento.CC, "10901A3456", False),
        (TipoDocumento.CC, "1234", False),
        (TipoDocumento.PPT, "25789456", True),
        (TipoDocumento.PASAPORTE, "AB123456", True),
        (TipoDocumento.PASAPORTE, "AB-123456", False),
    ],
)
def test_formato_del_numero_de_documento_segun_su_tipo(tipo, numero, valido):
    if valido:
        assert NumeroDocumento(tipo, numero).valor == numero
    else:
        with pytest.raises(DatosInvalidos):
            NumeroDocumento(tipo, numero)


def test_socio_con_telefono_invalido_no_se_crea():
    with pytest.raises(DatosInvalidos):
        Socio(TipoDocumento.CC, "1090000001", "Pedro", "Ríos", "30000003", bogota(2026, 1, 1))
