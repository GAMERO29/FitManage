from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Zapato:
    id: int
    referencia: str
    precio: Decimal
    stock: int


@dataclass
class Venta:
    cliente_nombre: str
    cliente_cedula: str
    zapato_id: int
    cantidad: int
    total: Decimal
