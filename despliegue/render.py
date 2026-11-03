"""Pide a Render que despliegue una imagen por su Deploy Hook (Guía 11, ADR N.° 11).

Uso:  RENDER_DEPLOY_HOOK=... python -m despliegue.render ghcr.io/gamero29/fitmanage:sha-<commit>

El hook es un secreto: lleva la llave del servicio en la URL. Este script lo lee del entorno,
nunca lo imprime (ni siquiera en un error) y solo acepta hooks de api.render.com por HTTPS.
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.parse
import urllib.request

PREFIJO_HOOK = "https://api.render.com/deploy/"
REPOSITORIO = "ghcr.io/gamero29/fitmanage:"


def url_de_despliegue(hook: str, imagen: str) -> str:
    if not hook.startswith(PREFIJO_HOOK):
        raise ValueError("El hook no es de api.render.com por HTTPS.")
    if not imagen.startswith(REPOSITORIO):
        raise ValueError(f"Solo se despliegan imágenes de {REPOSITORIO}*")
    separador = "&" if "?" in hook else "?"
    return f"{hook}{separador}imgURL={urllib.parse.quote(imagen, safe='')}"


def desplegar(imagen: str, hook: str, abrir=urllib.request.urlopen) -> int:
    peticion = urllib.request.Request(url_de_despliegue(hook, imagen), method="POST")
    try:
        with abrir(peticion, timeout=30) as respuesta:  # noqa: S310 # nosec B310
            print(f"Render aceptó el despliegue de {imagen} (HTTP {respuesta.status})")
            return 0
    except urllib.error.HTTPError as error:
        print(f"Render rechazó el despliegue de {imagen}: HTTP {error.code}")
    except urllib.error.URLError:
        print("No se pudo contactar a Render.")
    return 1


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    hook = os.environ.get("HOOK") or os.environ.get("RENDER_DEPLOY_HOOK", "")
    if len(argv) != 1 or not hook:
        print("Uso: RENDER_DEPLOY_HOOK=... python -m despliegue.render IMAGEN")
        return 2
    try:
        return desplegar(argv[0], hook)
    except ValueError as error:
        print(f"Despliegue cancelado: {error}")
        return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
