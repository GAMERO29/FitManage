"""Pruebas de la versión corregida con SQLite en memoria (biblioteca estándar)."""

import sqlite3
from decimal import Decimal

import pytest

from corregido import (
    PagoRechazado,
    ProductoNoEncontrado,
    ServicioVentas,
    StockInsuficiente,
    Venta,
    Zapato,
    leer_secreto,
)


class Sqlite:
    def __init__(self):
        self.cx = sqlite3.connect(":memory:")
        self.cx.executescript(
            "CREATE TABLE zapatos (id INTEGER PRIMARY KEY, referencia TEXT, precio TEXT, stock INT);"
            "CREATE TABLE ventas (cliente_id INT, zapato_id INT, cantidad INT, total TEXT);"
            "INSERT INTO zapatos VALUES (1, 'Z-01', '150000', 5);"
        )

    # RepositorioZapatos
    def obtener_por_referencia(self, referencia):
        fila = self.cx.execute(
            "SELECT id, precio, stock FROM zapatos WHERE referencia = ?", (referencia,)
        ).fetchone()
        return Zapato(fila[0], Decimal(fila[1]), fila[2]) if fila else None

    def descontar_stock(self, zapato_id, cantidad):
        self.cx.execute("UPDATE zapatos SET stock = stock - ? WHERE id = ?", (cantidad, zapato_id))

    # RepositorioVentas
    def registrar(self, venta: Venta):
        self.cx.execute("INSERT INTO ventas VALUES (?, ?, ?, ?)",
                        (venta.cliente_id, venta.zapato_id, venta.cantidad, str(venta.total)))

    # UnidadDeTrabajo
    def __enter__(self):
        return self

    def __exit__(self, tipo, *resto):
        self.cx.rollback() if tipo else self.cx.commit()

    def ventas(self):
        return self.cx.execute("SELECT * FROM ventas").fetchall()


class IvaGeneral:
    def tasa_iva(self):
        return Decimal("0.19")


class Pasarela:
    def __init__(self, aprueba=True):
        self.aprueba, self.cobros = aprueba, []

    def cobrar(self, monto, referencia_venta):
        self.cobros.append(monto)
        return self.aprueba


def servicio(db, pasarela=None):
    return ServicioVentas(db, db, pasarela or Pasarela(), IvaGeneral(), db)


def test_venta_calcula_total_con_iva_en_decimal_y_descuenta_stock():
    db = Sqlite()
    venta = servicio(db).procesar_venta(7, "Z-01", 2, cobrar_en_linea=False)
    assert venta.total == Decimal("357000.00")
    assert db.obtener_por_referencia("Z-01").stock == 3


def test_referencia_maliciosa_no_inyecta_sql():
    db = Sqlite()
    with pytest.raises(ProductoNoEncontrado):
        servicio(db).procesar_venta(7, "' OR '1'='1", 1, cobrar_en_linea=False)


def test_sin_stock_no_se_vende():
    with pytest.raises(StockInsuficiente):
        servicio(Sqlite()).procesar_venta(7, "Z-01", 9, cobrar_en_linea=False)


def test_cobro_rechazado_no_registra_la_venta():
    db = Sqlite()
    with pytest.raises(PagoRechazado):
        servicio(db, Pasarela(aprueba=False)).procesar_venta(7, "Z-01", 1, cobrar_en_linea=True)
    assert db.ventas() == []


def test_secreto_ausente_falla_en_lugar_de_usar_una_clave_por_defecto(monkeypatch):
    monkeypatch.delenv("PAYU_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        leer_secreto("PAYU_API_KEY")
