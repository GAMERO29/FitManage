"""Adaptador de salida con sqlite3 (biblioteca estándar). Los errores de la base no salen de aquí."""

from __future__ import annotations

import sqlite3
from decimal import Decimal

from nucleo_ventas import StockInsuficiente, Venta, Zapato


class AlmacenSqlite:
    """Implementa Catalogo y LibroDeVentas sobre la misma conexión."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._cx = conexion

    def obtener_por_referencia(self, referencia: str) -> Zapato | None:
        fila = self._cx.execute(
            "SELECT id, precio, stock FROM zapatos WHERE referencia = ?", (referencia,)
        ).fetchone()
        return Zapato(fila[0], Decimal(fila[1]), fila[2]) if fila else None

    def registrar(self, venta: Venta) -> None:
        try:
            with self._cx:  # una transacción: venta y stock, o nada
                actualizados = self._cx.execute(
                    "UPDATE zapatos SET stock = stock - ? WHERE id = ? AND stock >= ?",
                    (venta.cantidad, venta.zapato_id, venta.cantidad),
                ).rowcount
                if actualizados != 1:
                    raise StockInsuficiente(str(venta.zapato_id))
                self._cx.execute(
                    "INSERT INTO ventas (cliente_id, zapato_id, cantidad, total) VALUES (?, ?, ?, ?)",
                    (venta.cliente_id, venta.zapato_id, venta.cantidad, str(venta.total)),
                )
        except sqlite3.IntegrityError as error:
            raise StockInsuficiente(str(venta.zapato_id)) from error
