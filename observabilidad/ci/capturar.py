"""Captura el tablero de Grafana y una traza de Jaeger con Chromium (workflow Observabilidad).

Imprime cada PNG en base64 entre marcas, para poder sacarlo del log de la corrida sin publicar
artefactos.

    python observabilidad/ci/capturar.py grafana-apagon            # solo el tablero
    python observabilidad/ci/capturar.py grafana <trace_id>        # el tablero y una traza
"""

from __future__ import annotations

import base64
import os
import sys

from playwright.sync_api import sync_playwright

DESDE = os.environ.get("GRAFANA_DESDE", "now-10m")  # el simulacro de la Guía 14 usa now-45m
GRAFANA = f"http://127.0.0.1:3000/d/fitmanage-api/fitmanage-api?orgId=1&from={DESDE}&to=now&kiosk"
JAEGER = "http://127.0.0.1:16686/trace/{}"


def imprimir(nombre: str, png: bytes) -> None:
    print(f"----- INICIO {nombre} -----")
    print(base64.b64encode(png).decode())
    print(f"----- FIN {nombre} -----")


def main() -> None:
    nombre = sys.argv[1]
    trace_id = sys.argv[2] if len(sys.argv) > 2 else None
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 1600, "height": 1300})
        pagina.goto(GRAFANA, wait_until="networkidle")
        pagina.wait_for_timeout(8000)  # que terminen de dibujarse los paneles
        imprimir(f"{nombre}.png", pagina.screenshot(full_page=True))
        if trace_id:
            pagina.goto(JAEGER.format(trace_id), wait_until="networkidle")
            pagina.wait_for_timeout(3000)
            pagina.get_by_text("consultar_estado").first.click()  # abre los atributos del span
            pagina.wait_for_timeout(1500)
            imprimir("jaeger.png", pagina.screenshot(full_page=True))
        navegador.close()


if __name__ == "__main__":
    main()
