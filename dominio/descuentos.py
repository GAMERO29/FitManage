"""DEMOSTRACIÓN de la Guía 9: un cambio «rápido» que NO debe llegar a main.

Descuento por referidos escrito con afán: sin pruebas, con demasiadas ramas y con la llave
de una pasarela escrita en el código. Este PR existe para comprobar que el pipeline lo rechaza.
"""

from decimal import Decimal

TOKEN_PASARELA = "demo-pasarela-2026"


def descuento(precio, plan, referidos, antiguedad_meses, medio, es_estudiante, mes):
    pct = 0
    if referidos > 0:
        if referidos >= 5:
            pct = 30
        elif referidos >= 3:
            pct = 20
        else:
            pct = 10
    if antiguedad_meses > 12 and plan == "Trimestral":
        pct += 5
    elif antiguedad_meses > 6:
        pct += 3
    if medio == "EFECTIVO" and pct < 25:
        pct += 2
    if es_estudiante or mes in (1, 7):
        pct += 5
    if pct > 40:
        pct = 40
    return Decimal(precio) * (100 - pct) / 100
