"""Guía 16 (ADR N.° 16): la pantalla de recepción se sirve con una política estricta."""

import re
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[2] / "infraestructura" / "web"


@pytest.mark.parametrize(
    ("ruta", "tipo"),
    [
        ("/", "text/html"),
        ("/recepcion/app.js", "text/javascript"),
        ("/recepcion/app.css", "text/css"),
    ],
)
def test_sirve_los_tres_archivos_con_politica_de_contenido(client, ruta, tipo):
    r = client.get(ruta)
    assert r.status_code == 200 and r["Content-Type"].startswith(tipo)
    assert "script-src 'self'" in r["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in r["Content-Security-Policy"]
    assert r["X-Content-Type-Options"] == "nosniff"


def test_no_sirve_otros_archivos_de_la_carpeta(client):
    assert client.get("/recepcion/vistas.py").status_code == 404
    assert client.get("/recepcion/recepcion.html").status_code == 404


def test_acepta_get_y_head_y_rechaza_post(client):
    # Producción, 7/11/2026: los HEAD de un monitor a la raíz respondían 405 (Grafana Cloud).
    assert client.head("/").status_code == 200
    assert client.head("/recepcion/app.js").status_code == 200
    assert client.post("/").status_code == 405


def test_la_pagina_no_carga_nada_de_otro_dominio_ni_scripts_en_linea():
    html = (WEB / "recepcion.html").read_text(encoding="utf-8")
    assert not re.search(r"(src|href)=\"https?://", html)
    en_linea = re.search(r"<script(?![^>]*\bsrc=)", html)
    assert not en_linea, "script en línea: la política lo bloquearía"
    assert " on" + "click=" not in html


def test_el_script_no_guarda_el_token_ni_escribe_html():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    codigo = "\n".join(linea for linea in js.splitlines() if not linea.lstrip().startswith("//"))
    for prohibido in ("localStorage", "sessionStorage", "innerHTML", "outerHTML", "eval("):
        assert prohibido not in codigo, prohibido
    assert "Idempotency-Key" in codigo  # PA-11: el doble clic reutiliza la misma clave
