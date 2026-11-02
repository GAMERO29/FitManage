"""DEMOSTRACIÓN de la Guía 9: un cambio que NO debe llegar a main.

Segundo intento: ya pasa ruff, bandit y radon, pero sigue sin una sola prueba.
"""

from decimal import Decimal

TOPES_POR_REFERIDOS = ((5, 30), (3, 20), (1, 10))


def porcentaje_por_referidos(referidos: int) -> int:
    for minimo, pct in TOPES_POR_REFERIDOS:
        if referidos >= minimo:
            return pct
    return 0


def descuento(precio: Decimal, referidos: int, es_estudiante: bool) -> Decimal:
    pct = porcentaje_por_referidos(referidos) + (5 if es_estudiante else 0)
    return precio * (100 - min(pct, 40)) / 100
