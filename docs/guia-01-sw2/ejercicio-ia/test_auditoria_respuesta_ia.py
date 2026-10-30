"""Pruebas que demuestran los defectos de la respuesta de la IA (Ejercicio 6).

Cada prueba pasa cuando el defecto existe: documentan el comportamiento real de respuesta_ia.py.
"""

import importlib
import sys
from decimal import Decimal

import pytest

import respuesta_ia as ia


class ZapatosFalsos(ia.RepositorioZapatos):
    def __init__(self, precio, stock=5):
        self.precio, self.stock = precio, stock

    def obtener_por_referencia(self, referencia):
        return {"id": 1, "precio": self.precio, "stock": self.stock}


class VentasFalsas(ia.RepositorioVentas):
    def __init__(self):
        self.registradas = []

    def registrar(self, venta):
        self.registradas.append(venta)


class PasarelaQueRechaza(ia.PasarelaPago):
    def cobrar(self, monto):
        return False


def test_precio_decimal_de_postgresql_rompe_el_calculo():
    # psycopg2 entrega las columnas NUMERIC como Decimal; Decimal * float no está definido.
    servicio = ia.ServicioVentas(ZapatosFalsos(Decimal("150000")), VentasFalsas(), PasarelaQueRechaza())
    with pytest.raises(TypeError):
        servicio.procesar_transaccion_venta("Cliente Ficticio", "0000000000", "Z-01", 1, "EFECTIVO")


def test_la_venta_queda_registrada_aunque_el_cobro_falle():
    ventas = VentasFalsas()
    servicio = ia.ServicioVentas(ZapatosFalsos(150000.0), ventas, PasarelaQueRechaza())
    servicio.procesar_transaccion_venta("Cliente Ficticio", "0000000000", "Z-01", 1, "PAYU")
    assert len(ventas.registradas) == 1


def test_no_valida_el_stock_disponible():
    ventas = VentasFalsas()
    servicio = ia.ServicioVentas(ZapatosFalsos(150000.0, stock=0), ventas, PasarelaQueRechaza())
    servicio.procesar_transaccion_venta("Cliente Ficticio", "0000000000", "Z-01", 3, "EFECTIVO")
    assert ventas.registradas[0]["cantidad"] == 3


def test_referencia_inexistente_produce_error_tecnico():
    class CursorVacio:
        def execute(self, *args):
            pass

        def fetchone(self):
            return None

    class ConexionVacia:
        def cursor(self):
            return CursorVacio()

    repo = ia.RepositorioZapatosPostgres(ConexionVacia())
    with pytest.raises(TypeError):
        repo.obtener_por_referencia("NO-EXISTE")


def test_sin_variable_de_entorno_se_usa_la_clave_expuesta(monkeypatch):
    monkeypatch.delenv("PAYU_API_KEY", raising=False)
    modulo = importlib.reload(sys.modules["respuesta_ia"])
    assert modulo.PasarelaPayU().api_key == "PROD_SECRET_KEY_EXPOSED_12345"
