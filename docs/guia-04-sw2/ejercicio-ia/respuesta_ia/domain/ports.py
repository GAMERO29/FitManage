from abc import ABC, abstractmethod
from decimal import Decimal

from domain.entities import Venta, Zapato


class ZapatoRepositoryPort(ABC):
    @abstractmethod
    def find_by_referencia(self, referencia: str) -> Zapato: ...


class VentaRepositoryPort(ABC):
    @abstractmethod
    def save(self, venta: Venta) -> None: ...


class PaymentGatewayPort(ABC):
    @abstractmethod
    def charge(self, amount: Decimal) -> bool: ...


class TaxCalculatorPort(ABC):
    @abstractmethod
    def calculate(self, subtotal: Decimal) -> Decimal: ...


class LoggerPort(ABC):
    @abstractmethod
    def info(self, message: str) -> None: ...


class UnitOfWorkPort(ABC):
    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...
