"""Software III · Guía 12: los mismos casos, con el mismo estado inicial, para las dos versiones.

    python3 -m pytest -p no:cacheprovider -rA docs/sw3/g12/experimento

Estado inicial común: Ana tiene un pago de octubre (Laura, 7 oct) y uno de noviembre registrado
por Laura el 1 de noviembre a las 18:00. Ahora son las 10:00 del 2 de noviembre en Bogotá.
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import transaction_script as ts  # noqa: E402

from aplicacion.pagos import AnulacionPagoService  # noqa: E402
from dominio.errores import MotivoRequerido, PagoNoAnulable, PermisoDenegado  # noqa: E402
from dominio.modelos import (  # noqa: E402
    ZONA_HORARIA,
    MedioPago,
    Pago,
    Rol,
    Socio,
    TipoDocumento,
    Usuario,
)

AHORA = datetime(2026, 11, 2, 10, 0, tzinfo=ZONA_HORARIA)
ANA = Socio(TipoDocumento.CC, "1090000011", "Ana", "Prueba Demo", "3001234567", AHORA)
CARLOS = Usuario("Carlos Demo", "carlos@demo.local", Rol.ADMINISTRADOR)
LAURA = Usuario("Laura Demo", "laura@demo.local", Rol.RECEPCIONISTA)


class Reloj:
    def ahora(self):
        return AHORA

    def hoy(self):
        return AHORA.date()


class Pagos:
    def __init__(self, *pagos):
        self.p = {x.id: x for x in pagos}

    def obtener(self, pago_id):
        return self.p.get(pago_id)

    def vigentes_de(self, socio):
        return [x for x in self.p.values() if x.socio.id == socio.id and x.esta_vigente()]

    def guardar(self, pago):
        self.p[pago.id] = pago


def pagos_iniciales():
    def pago(inicia, vence, registrado_en):
        return Pago(
            ANA,
            uuid4(),
            Decimal("80000"),
            30,
            MedioPago.EFECTIVO,
            None,
            inicia,
            vence,
            LAURA,
            registrado_en,
        )

    octubre = pago(
        date(2026, 10, 7), date(2026, 11, 5), datetime(2026, 10, 7, 8, 0, tzinfo=ZONA_HORARIA)
    )
    noviembre = pago(
        date(2026, 11, 6), date(2026, 12, 5), datetime(2026, 11, 1, 18, 0, tzinfo=ZONA_HORARIA)
    )
    return octubre, noviembre


class DomainModel:
    nombre = "domain-model"

    def __init__(self):
        self.octubre, self.noviembre = pagos_iniciales()
        self.servicio = AnulacionPagoService(Pagos(self.octubre, self.noviembre), Reloj())

    def anular_ultimo(self, usuario, motivo):
        return self.servicio.anular_ultimo(ANA, usuario, motivo)

    def anular(self, pago, usuario, motivo):
        return self.servicio.anular(getattr(self, pago).id, usuario, motivo)

    def anular_para_cambio(self, pago, usuario, motivo):
        return self.servicio.anular(
            getattr(self, pago).id, usuario, motivo, para_cambio_de_plan=True
        )

    def estados(self):
        return (self.octubre.estado.value, self.noviembre.estado.value)


class TransactionScript:
    nombre = "transaction-script"

    def __init__(self):
        def fila(p):
            return {
                "id": p.id,
                "socio_id": ANA.id,
                "inicia": p.fecha_inicio,
                "estado": "VIGENTE",
                "registrado_en": p.registrado_en,
                "registrado_por_id": LAURA.id,
                "motivo": None,
            }

        self.filas = [fila(p) for p in pagos_iniciales()]
        self.octubre, self.noviembre = self.filas

    @staticmethod
    def _u(usuario):
        return {"id": usuario.id, "rol": usuario.rol.value, "activo": usuario.activo}

    def anular_ultimo(self, usuario, motivo):
        return ts.anular_ultimo(self.filas, ANA.id, self._u(usuario), motivo, AHORA)

    def anular(self, pago, usuario, motivo):
        return ts.anular_por_id(
            self.filas, getattr(self, pago)["id"], self._u(usuario), motivo, AHORA
        )

    def anular_para_cambio(self, pago, usuario, motivo):
        pago_id = getattr(self, pago)["id"]
        return ts.anular_para_cambio_de_plan(self.filas, pago_id, self._u(usuario), motivo, AHORA)

    def estados(self):
        return (self.octubre["estado"], self.noviembre["estado"])


@pytest.fixture(params=[TransactionScript, DomainModel], ids=lambda c: c.nombre)
def v(request):
    return request.param()


def test_caso_1_el_administrador_anula_el_ultimo(v):
    v.anular_ultimo(CARLOS, "Se registró el plan equivocado")
    assert v.estados() == ("VIGENTE", "ANULADO")


def test_caso_2_no_se_anula_un_pago_que_no_es_el_ultimo(v):
    with pytest.raises(PagoNoAnulable):
        v.anular("octubre", CARLOS, "Se registró el plan equivocado")
    assert v.estados() == ("VIGENTE", "VIGENTE")


def test_caso_3_la_recepcionista_no_anula_su_pago_de_ayer_pero_si_lo_cambia_de_plan(v):
    with pytest.raises(PermisoDenegado):
        v.anular("noviembre", LAURA, "Se registró el plan equivocado")
    assert v.estados() == ("VIGENTE", "VIGENTE")
    v.anular_para_cambio("noviembre", LAURA, "La socia pidió un plan más corto")
    assert v.estados() == ("VIGENTE", "ANULADO")


# CR-02 (Guía 10): el motivo necesita al menos 5 caracteres, por cualquier entrada.
@pytest.mark.parametrize("entrada", ["anular_ultimo", "anular", "anular_para_cambio"])
def test_cr02_un_motivo_de_menos_de_5_caracteres_no_anula(v, entrada):
    with pytest.raises(MotivoRequerido):
        if entrada == "anular_ultimo":
            v.anular_ultimo(CARLOS, "  x  ")
        else:
            getattr(v, entrada)("noviembre", CARLOS, "  x  ")
    assert v.estados() == ("VIGENTE", "VIGENTE")
