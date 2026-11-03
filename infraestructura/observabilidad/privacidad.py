"""Ley 1581 de 2012 aplicada a la telemetría: ni documentos ni teléfonos en claro (ADR N.° 13)."""

from __future__ import annotations

import re

from django.utils.crypto import salted_hmac

# La consulta de recepción lleva el documento en la URL; cualquier log que la copie la redacta.
_RUTA_ESTADO = re.compile(r"/estados/[^/\s\"']+/[^/\s\"'?]+")
# Cédulas, pasaportes y celulares colombianos tienen 7 dígitos o más; un puerto o una IP, no.
_CIFRAS_LARGAS = re.compile(r"\d{7,}")


def seudonimo(tipo: str, numero: str) -> str:
    """HMAC con la SECRET_KEY: permite agrupar las consultas de un mismo socio sin saber quién es.

    Usa otra sal que la huella del celular (`presentacion.huella_documento`), para que un dato de
    la telemetría no sirva para cruzarlo con la caché de un teléfono.
    """
    return salted_hmac("fitmanage.telemetria", f"{tipo}:{numero}", algorithm="sha256").hexdigest()[
        :12
    ]


def redactar(texto: str) -> str:
    texto = _RUTA_ESTADO.sub("/estados/{tipoDocumento}/{numeroDocumento}", texto)
    return _CIFRAS_LARGAS.sub("[redactado]", texto)
