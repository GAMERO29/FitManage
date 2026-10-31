from decimal import Decimal

from domain.ports import TaxCalculatorPort


class ColombianTaxCalculator(TaxCalculatorPort):
    IVA = Decimal("0.19")

    def calculate(self, subtotal: Decimal) -> Decimal:
        return subtotal * self.IVA
