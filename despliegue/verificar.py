"""Healthcheck posterior al despliegue (Guía 11, ADR N.° 11).

Uso:  URL_PRODUCCION=https://... python -m despliegue.verificar VERSION_ESPERADA [--espera-max 600]

La URL sale del entorno (la variable URL_PRODUCCION del environment de GitHub) y no de la
línea de comandos: así nadie puede apuntar el script a otro host pasándole un argumento, y
además solo se aceptan https://*.onrender.com o esta misma máquina (SonarCloud S8703).

Pasa (código 0) solo si /api/v1/salud responde 200 con estado "ok" y la versión esperada en
3 consultas seguidas, y si una ruta protegida sigue exigiendo token (401). Si en el tiempo
máximo no lo logra, sale con código 1 y el pipeline hace rollback.

Que la versión coincida importa: Render mantiene viva la versión anterior mientras la nueva
no pasa su propio healthcheck, así que un 200 por sí solo no prueba que el despliegue llegó.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

SEGUIDAS = 3


@dataclass
class Lectura:
    estado_http: int
    version: str | None


def url_permitida(url_base: str) -> bool:
    """https://<servicio>.onrender.com, o HTTP contra esta máquina (pruebas). Nada más."""
    partes = urllib.parse.urlsplit(url_base)
    if partes.scheme == "https":
        return (partes.hostname or "").endswith(".onrender.com")
    return partes.scheme == "http" and partes.hostname in {"127.0.0.1", "localhost"}


def leer_salud(url_base: str, timeout: float = 10) -> Lectura:
    try:
        # verificar() solo llega aquí con una URL que pasó url_permitida(); de ahí el nosec.
        with urllib.request.urlopen(f"{url_base}/api/v1/salud", timeout=timeout) as r:  # noqa: S310 # nosec B310
            cuerpo = json.loads(r.read())
            version = cuerpo.get("version") if cuerpo.get("estado") == "ok" else None
            return Lectura(r.status, version)
    except urllib.error.HTTPError as error:
        return Lectura(error.code, None)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return Lectura(0, None)


def ruta_protegida_exige_token(url_base: str, timeout: float = 10) -> bool:
    try:
        urllib.request.urlopen(f"{url_base}/api/v1/estados", timeout=timeout)  # noqa: S310 # nosec B310
    except urllib.error.HTTPError as error:
        return error.code == 401
    except (urllib.error.URLError, TimeoutError):
        return False
    return False  # 200 sin token sería un hueco de seguridad


def verificar(url_base: str, esperada: str, espera_max: float, pausa: float = 10) -> bool:
    url_base = url_base.rstrip("/")
    if not url_permitida(url_base):
        print(f"FALLA: {url_base} no es https://*.onrender.com")
        return False
    limite = time.monotonic() + espera_max
    seguidas = 0
    while time.monotonic() < limite:
        lectura = leer_salud(url_base)
        if lectura.estado_http == 200 and lectura.version == esperada:
            seguidas += 1
            print(f"OK {seguidas}/{SEGUIDAS}: versión {esperada[:12]} en línea")
            if seguidas == SEGUIDAS:
                if ruta_protegida_exige_token(url_base):
                    print("OK: /api/v1/estados sigue exigiendo token (401)")
                    return True
                print("FALLA: /api/v1/estados respondió sin exigir token")
                return False
        else:
            seguidas = 0
            print(f"Esperando: HTTP {lectura.estado_http}, versión en línea {lectura.version}")
        time.sleep(pausa)
    print(f"FALLA: la versión {esperada[:12]} no quedó sana en {espera_max:.0f} s")
    return False


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("version_esperada")
    p.add_argument("--espera-max", type=float, default=600)
    p.add_argument("--pausa", type=float, default=10)
    a = p.parse_args(argv)
    url_base = os.environ.get("URL_PRODUCCION", "")
    return 0 if verificar(url_base, a.version_esperada, a.espera_max, a.pausa) else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
