"""Ejercicio 5 de la Guía 13: el «hash» de la cédula que propuso la IA se revierte en segundos.

La IA guardaba en el span y en el log `sha256(cedula)[:12]`, sin clave. Quien lea la telemetría
puede probar todas las cédulas posibles y encontrar la que da ese hash. Este script lo hace para
un rango de 10 millones de documentos (las cédulas que empiezan por 109, típicas de Norte de
Santander) y mide cuánto tarda.

    python docs/guia-13-sw2/ejercicio-ia/revertir_hash.py 1093445566
"""

from __future__ import annotations

import hashlib
import sys
import time


def hash_de_la_ia(cedula: str) -> str:
    return hashlib.sha256(cedula.encode()).hexdigest()[:12]


def revertir(objetivo: str, desde: int, hasta: int) -> str | None:
    for numero in range(desde, hasta):
        candidato = str(numero)
        if hashlib.sha256(candidato.encode()).hexdigest()[:12] == objetivo:
            return candidato
    return None


def main() -> None:
    cedula = sys.argv[1] if len(sys.argv) > 1 else "1093445566"
    visto_en_el_log = hash_de_la_ia(cedula)
    print(f"En el log aparece socio_hash={visto_en_el_log!r}")
    inicio = time.perf_counter()
    encontrada = revertir(visto_en_el_log, 1_090_000_000, 1_100_000_000)
    print(f"Cédula recuperada: {encontrada}  ({time.perf_counter() - inicio:.1f} s, un solo núcleo)")


if __name__ == "__main__":
    main()
