"""Captura el tablero de Grafana y una traza de Jaeger con Chromium (workflow Observabilidad).

Imprime cada PNG en base64 entre marcas, para poder sacarlo del log de la corrida sin publicar
artefactos. Uso: python observabilidad/ci/capturar.py <trace_id>
"""

from __future__ import annotations

import base64
import sys

from playwright.sync_api import sync_playwright

GRAFANA = "http://127.0.0.1:3000/d/fitmanage-api/fitmanage-api?orgId=1&from=now-10m&to=now&kiosk"
JAEGER = "http://127.0.0.1:16686/trace/{}"


def imprimir(nombre: str, png: bytes) -> None:
    print(f"----- INICIO {nombre} -----")
    print(base64.b64encode(png).decode())
    print(f"----- FIN {nombre} -----")


def main() -> None:
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 1600, "height": 1000})
        pagina.goto(GRAFANA, wait_until="networkidle")
        pagina.wait_for_timeout(8000)  # que terminen de dibujarse los paneles
        imprimir("grafana.png", pagina.screenshot(full_page=True))
        if len(sys.argv) > 1:
            pagina.goto(JAEGER.format(sys.argv[1]), wait_until="networkidle")
            pagina.wait_for_timeout(4000)
            imprimir("jaeger.png", pagina.screenshot(full_page=True))
        navegador.close()


if __name__ == "__main__":
    main()
