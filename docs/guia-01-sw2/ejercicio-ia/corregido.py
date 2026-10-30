"""Refactorización corregida por el equipo tras auditar la respuesta de la IA (Ejercicio 6).

El servicio depende solo de abstracciones (DIP); las implementaciones concretas se inyectan.
Solo usa la biblioteca estándar: no agrega dependencias ni licencias nuevas.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol


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
    cliente_id: int  # se referencia al cliente; el nombre y la cédula viven en su propia tabla
    zapato_id: int
    cantidad: int
    total: Decimal


class RepositorioZapatos(Protocol):
    def obtener_por_referencia(self, referencia: str) -> Zapato | None: ...

    def descontar_stock(self, zapato_id: int, cantidad: int) -> None: ...


class RepositorioVentas(Protocol):
    def registrar(self, venta: Venta) -> None: ...


class PasarelaPago(Protocol):
    def cobrar(self, monto: Decimal, referencia_venta: str) -> bool: ...


class UnidadDeTrabajo(Protocol):
    def __enter__(self) -> UnidadDeTrabajo: ...

    def __exit__(self, *excepcion) -> None: ...


class PoliticaImpuestos(Protocol):
    def tasa_iva(self) -> Decimal: ...


CENTAVOS = Decimal("0.01")


class ServicioVentas:
    def __init__(self, zapatos: RepositorioZapatos, ventas: RepositorioVentas,
                 pasarela: PasarelaPago, impuestos: PoliticaImpuestos,
                 transaccion: UnidadDeTrabajo) -> None:
        self._zapatos = zapatos
        self._ventas = ventas
        self._pasarela = pasarela
        self._impuestos = impuestos
        self._transaccion = transaccion

    def procesar_venta(self, cliente_id: int, referencia: str, cantidad: int,
                       cobrar_en_linea: bool) -> Venta:
        zapato = self._zapatos.obtener_por_referencia(referencia)
        if zapato is None:
            raise ProductoNoEncontrado(referencia)
        if cantidad <= 0 or cantidad > zapato.stock:
            raise StockInsuficiente(referencia)
        total = (zapato.precio * cantidad * (1 + self._impuestos.tasa_iva())).quantize(
            CENTAVOS, rounding=ROUND_HALF_UP)
        venta = Venta(cliente_id, zapato.id, cantidad, total)
        if cobrar_en_linea and not self._pasarela.cobrar(total, referencia):
            raise PagoRechazado(referencia)
        with self._transaccion:
            self._ventas.registrar(venta)
            self._zapatos.descontar_stock(zapato.id, cantidad)
        return venta


def leer_secreto(nombre: str) -> str:
    """Los secretos vienen del entorno o de un gestor de secretos; sin valor por defecto."""
    valor = os.environ.get(nombre)
    if not valor:
        raise RuntimeError(f"Falta la variable de entorno {nombre}.")
    return valor
