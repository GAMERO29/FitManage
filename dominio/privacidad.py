"""Mínimo privilegio sobre datos personales (Ley 1581 de 2012): cómo se muestra un documento.

Lo usan la API y los modelos de lectura; vive en el dominio para que ninguno de los dos dependa
del otro (Software III, Guía 07: rompía el ciclo infraestructura.api ↔ infraestructura.consultas).
"""

from __future__ import annotations

from dominio.modelos import TipoDocumento


def documento_enmascarado(tipo: TipoDocumento, numero: str) -> str:
    """«CC 1090000044» → «CC ******0044»: basta para confirmar a quién se atiende."""
    return f"{tipo.value} {'*' * (len(numero) - 4)}{numero[-4:]}"
