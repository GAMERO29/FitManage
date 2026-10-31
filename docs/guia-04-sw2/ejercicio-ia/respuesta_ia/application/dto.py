from dataclasses import dataclass
from decimal import Decimal


@dataclass
class VentaRequestDTO:
    cliente_nombre: str
    cliente_cedula: str
    referencia_zapato: str
    cantidad: int
    metodo_pago: str


@dataclass
class VentaResponseDTO:
    zapato_id: int
    cantidad: int
    total: Decimal
