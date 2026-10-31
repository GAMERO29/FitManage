"""Núcleo de la venta: reglas y puertos. No importa ninguna librería de infraestructura."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol

CENTAVOS = Decimal("0.01")


class ErrorDeVenta(Exception):
    pass


class ProductoNoEncontrado(ErrorDeVenta):
    pass


class StockInsuficiente(ErrorDeVenta):
    pass


class PagoRechazado(ErrorDeVenta):
    pass


@dataclass(frozen=True)
class Zapato:
    id: int
    precio: Decimal
    stock: int


@dataclass(frozen=True)
class Venta:
    cliente_id: int
    zapato_id: int
    cantidad: int
    total: Decimal


class Catalogo(Protocol):
    """Puerto de salida: leer productos."""

    def obtener_por_referencia(self, referencia: str) -> Zapato | None: ...


class LibroDeVentas(Protocol):
    """Puerto de salida: guarda la venta y descuenta el stock en una sola transacción."""

    def registrar(self, venta: Venta) -> None: ...


class PasarelaPago(Protocol):
    """Puerto de salida: cobrar en línea."""

    def cobrar(self, monto: Decimal, referencia: str) -> bool: ...


class ProcesarVenta:
    """Caso de uso (puerto de entrada). Una clase basta: no hay dos implementaciones."""

    def __init__(self, catalogo: Catalogo, ventas: LibroDeVentas, pasarela: PasarelaPago,
                 tasa_iva: Decimal) -> None:
        self._catalogo = catalogo
        self._ventas = ventas
        self._pasarela = pasarela
        self._tasa_iva = tasa_iva

    def ejecutar(self, cliente_id: int, referencia: str, cantidad: int,
                 cobrar_en_linea: bool) -> Venta:
        zapato = self._catalogo.obtener_por_referencia(referencia)
        if zapato is None:
            raise ProductoNoEncontrado(referencia)
        if cantidad <= 0 or cantidad > zapato.stock:
            raise StockInsuficiente(referencia)
        total = (zapato.precio * cantidad * (1 + self._tasa_iva)).quantize(
            CENTAVOS, rounding=ROUND_HALF_UP)
        if cobrar_en_linea and not self._pasarela.cobrar(total, referencia):
            raise PagoRechazado(referencia)
        venta = Venta(cliente_id, zapato.id, cantidad, total)
        self._ventas.registrar(venta)
        return venta
