"""Ejercicio 5 con el fragmento de ventas: el núcleo se prueba con dobles, sin ninguna base de datos."""

from decimal import Decimal

import pytest

from nucleo_ventas import PagoRechazado, ProcesarVenta, ProductoNoEncontrado, StockInsuficiente, Zapato


class CatalogoFalso:
    def __init__(self, *zapatos):
        self.zapatos = {z.id: z for z in zapatos}

    def obtener_por_referencia(self, referencia):
        return self.zapatos.get(int(referencia.split("-")[1]))


class LibroFalso:
    def __init__(self):
        self.ventas = []

    def registrar(self, venta):
        self.ventas.append(venta)


class Pasarela:
    def __init__(self, aprueba):
        self.aprueba = aprueba

    def cobrar(self, monto, referencia):
        return self.aprueba


def caso(aprueba=True, stock=5):
    libro = LibroFalso()
    uso = ProcesarVenta(CatalogoFalso(Zapato(1, Decimal("150000"), stock)), libro,
                        Pasarela(aprueba), Decimal("0.19"))
    return uso, libro


def test_calcula_el_total_con_iva_en_decimal():
    uso, libro = caso()
    assert uso.ejecutar(7, "Z-1", 2, cobrar_en_linea=False).total == Decimal("357000.00")
    assert len(libro.ventas) == 1


def test_producto_inexistente():
    uso, _ = caso()
    with pytest.raises(ProductoNoEncontrado):
        uso.ejecutar(7, "Z-9", 1, cobrar_en_linea=False)


def test_sin_stock_no_se_vende():
    uso, libro = caso(stock=1)
    with pytest.raises(StockInsuficiente):
        uso.ejecutar(7, "Z-1", 2, cobrar_en_linea=False)
    assert libro.ventas == []


def test_cobro_rechazado_no_registra_la_venta():
    uso, libro = caso(aprueba=False)
    with pytest.raises(PagoRechazado):
        uso.ejecutar(7, "Z-1", 1, cobrar_en_linea=True)
    assert libro.ventas == []
