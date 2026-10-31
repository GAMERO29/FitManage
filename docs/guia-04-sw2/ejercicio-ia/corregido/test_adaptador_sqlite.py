import sqlite3
from decimal import Decimal

import pytest

from adaptador_sqlite import AlmacenSqlite
from nucleo_ventas import ProcesarVenta, ProductoNoEncontrado, StockInsuficiente, Venta


class PasarelaQueAprueba:
    def cobrar(self, monto, referencia):
        return True


@pytest.fixture
def almacen():
    cx = sqlite3.connect(":memory:")
    cx.executescript(
        "CREATE TABLE zapatos (id INTEGER PRIMARY KEY, referencia TEXT, precio TEXT, stock INT);"
        "CREATE TABLE ventas (cliente_id INT, zapato_id INT, cantidad INT, total TEXT);"
        "INSERT INTO zapatos VALUES (1, 'Z-01', '150000', 5);"
    )
    return AlmacenSqlite(cx), cx


def test_venta_completa_contra_sqlite(almacen):
    repo, cx = almacen
    uso = ProcesarVenta(repo, repo, PasarelaQueAprueba(), Decimal("0.19"))
    assert uso.ejecutar(7, "Z-01", 2, cobrar_en_linea=True).total == Decimal("357000.00")
    assert cx.execute("SELECT stock FROM zapatos").fetchone()[0] == 3


def test_referencia_maliciosa_no_encuentra_nada(almacen):
    repo, _ = almacen
    uso = ProcesarVenta(repo, repo, PasarelaQueAprueba(), Decimal("0.19"))
    with pytest.raises(ProductoNoEncontrado):
        uso.ejecutar(7, "' OR '1'='1", 1, cobrar_en_linea=False)


def test_el_adaptador_no_deja_stock_negativo_aunque_llegue_una_venta_vieja(almacen):
    repo, cx = almacen
    with pytest.raises(StockInsuficiente):
        repo.registrar(Venta(7, 1, 9, Decimal("1")))
    assert cx.execute("SELECT count(*) FROM ventas").fetchone()[0] == 0
