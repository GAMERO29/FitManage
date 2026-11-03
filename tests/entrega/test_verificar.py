"""El healthcheck posterior al despliegue, contra un servidor HTTP falso en localhost."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from despliegue.verificar import main, ruta_protegida_exige_token


class Servidor:
    def __init__(self, version: str = "abc", estados_status: int = 401, salud_status: int = 200):
        self.version, self.estados_status, self.salud_status = version, estados_status, salud_status
        fuera = self

        class Manejador(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                if self.path == "/api/v1/salud":
                    cuerpo = {"estado": "ok", "hora": "x", "version": fuera.version}
                    self._responder(fuera.salud_status, cuerpo)
                else:
                    self._responder(fuera.estados_status, {"codigo": "NO_AUTENTICADO"})

            def _responder(self, status, cuerpo):
                datos = json.dumps(cuerpo).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(datos)

            def log_message(self, *args):
                pass

        self.http = HTTPServer(("127.0.0.1", 0), Manejador)
        self.url = f"http://127.0.0.1:{self.http.server_port}"
        threading.Thread(target=self.http.serve_forever, daemon=True).start()


@pytest.fixture
def servidor():
    s = Servidor()
    yield s
    s.http.shutdown()


def correr(servidor, esperada="abc"):
    return lanzar(servidor.url, esperada, 0.5)


def lanzar(url, esperada="abc", espera=0.3):
    import os

    os.environ["URL_PRODUCCION"] = url
    try:
        return main([esperada, "--espera-max", str(espera), "--pausa", "0.01"])
    finally:
        del os.environ["URL_PRODUCCION"]


def test_pasa_con_la_version_esperada_y_la_ruta_protegida(servidor):
    assert correr(servidor) == 0


def test_falla_si_sigue_en_linea_la_version_anterior(servidor):
    """Render conserva la versión vieja si la nueva no arranca: un 200 no basta."""
    servidor.version = "vieja"
    assert correr(servidor, esperada="nueva") == 1


def test_falla_si_la_salud_responde_503(servidor):
    servidor.salud_status = 503
    assert correr(servidor) == 1


def test_falla_si_una_ruta_protegida_responde_sin_token(servidor):
    servidor.estados_status = 200
    assert correr(servidor) == 1


def test_falla_si_el_servicio_no_existe():
    assert lanzar("http://127.0.0.1:9") == 1


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc",
        "http://fitmanage-svol.onrender.com",
        "https://evil.example.com",
        "https://onrender.com.evil.example",
        "",
    ],
)
def test_rechaza_cualquier_destino_que_no_sea_render_por_https(url):
    assert lanzar(url, espera=0.1) == 1


def test_acepta_el_servicio_de_render():
    from despliegue.verificar import url_permitida

    assert url_permitida("https://fitmanage-svol.onrender.com")


def test_si_no_hay_respuesta_la_ruta_protegida_no_cuenta_como_protegida():
    assert ruta_protegida_exige_token("http://127.0.0.1:9", timeout=0.2) is False


def test_explica_por_que_espera(servidor, capsys):
    servidor.salud_status = 503
    correr(servidor)
    assert "HTTP 503" in capsys.readouterr().out


def test_una_respuesta_que_no_es_json_se_explica(capsys):
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Html(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<html>Service waking up</html>")

        def log_message(self, *args):
            pass

    http = HTTPServer(("127.0.0.1", 0), Html)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    assert lanzar(f"http://127.0.0.1:{http.server_port}") == 1
    http.shutdown()
    assert "no es JSON" in capsys.readouterr().out
