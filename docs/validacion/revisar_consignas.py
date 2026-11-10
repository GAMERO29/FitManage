"""Guía II-06 · ¿Alguna consigna del protocolo revela la ruta de la solución?

Compara cada consigna con los textos de botones, enlaces, menús y títulos de la interfaz
(los literales que cierran una llamada `h(...)` o `enlace(...)` en app.js, más TITULOS).
Es una revisión mecánica: no reemplaza el ensayo con una persona. Uso: python revisar_consignas.py
"""

import re
import sys
import unicodedata
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "infraestructura" / "web" / "app.js"

# Las consignas viven aquí y en protocolo.md; si cambian, cambian en los dos lugares.
CONSIGNAS = {
    "T1": "Llega Ana, una socia, con su cédula 1090000011 y quiere pasar a entrenar. Averigüe si puede hacerlo y hasta qué día.",
    "T2": "Ana quiere pagar otro mes. Le muestra en el celular una transferencia por Nequi con el número M123456. Deje el pago listo para que el sistema lo reconozca.",
    "T3": "Cinco minutos después Ana vuelve: quería quince días, no un mes, y usted ya le cobró el mes. Deje las cosas como deben quedar.",
    "T4": "Mientras atiende a la persona que sigue en la fila, la pantalla muestra algo distinto de lo habitual. Cuente qué hace con la persona que espera.",
    "T5": "No recuerda cómo se corrige un cobro equivocado. Encuentre cómo hacerlo con el material que tiene a mano, sin preguntarme.",
    "A1": "El dueño cree que hoy alguien deshizo un cobro en el mostrador. Averigüe quién fue, a qué hora y qué razón dio.",
    "A2": "Desde el lunes, el plan de un mes cuesta 80.000. Haga el cambio y explique qué pasa con quienes ya pagaron.",
}
# Palabras del oficio que la persona usa igual sin el sistema: no cuentan como pista.
# «días» quedó aquí después de la primera revisión: la socia dice «quince días», y la interfaz muestra «30 días».
DEL_DOMINIO = {"dias", "socio", "socios", "pago", "pagos", "plan", "planes", "nequi", "mensual", "quincenal"}


def sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def etiquetas() -> set[str]:
    fuente = APP.read_text(encoding="utf-8")
    literales = re.findall(r',\s*"([^"{}$<>]{3,40})"\s*\)', fuente)
    titulos = re.findall(r'\w+:\s*"([^"]+)"', re.search(r"const TITULOS = \{(.*?)\};", fuente).group(1))
    return {t.strip() for t in literales + titulos if not t.startswith(("#", "/", "."))}


def main() -> int:
    textos = etiquetas()
    print(f"Textos de la interfaz revisados: {len(textos)}")
    pistas = 0
    for clave, consigna in CONSIGNAS.items():
        c = sin_tildes(consigna)
        encontradas = sorted(
            t for t in textos
            if sin_tildes(t) not in DEL_DOMINIO and re.search(rf"\b{re.escape(sin_tildes(t))}\b", c)
        )
        pistas += len(encontradas)
        print(f"{clave}: {'sin pistas' if not encontradas else 'PISTA: ' + ', '.join(encontradas)}")
    print(f"Resumen: {pistas} pistas en {len(CONSIGNAS)} consignas.")
    return 1 if pistas else 0


if __name__ == "__main__":
    sys.exit(main())
