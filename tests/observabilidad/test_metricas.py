"""/metrics: Prometheus lo lee con un token; nadie más debe ver el mapa de tráfico del gimnasio."""

import pytest

TOKEN = "token-de-prometheus-de-prueba"


@pytest.fixture
def con_token(monkeypatch):
    monkeypatch.setenv("FITMANAGE_METRICAS_TOKEN", TOKEN)


def test_sin_token_configurado_el_endpoint_no_existe(client, monkeypatch):
    monkeypatch.delenv("FITMANAGE_METRICAS_TOKEN", raising=False)
    assert client.get("/metrics").status_code == 404


@pytest.mark.parametrize("encabezado", [None, "Bearer otro", f"Basic {TOKEN}x"])
def test_sin_el_token_correcto_es_401(client, con_token, encabezado):
    extra = {"HTTP_AUTHORIZATION": encabezado} if encabezado else {}
    r = client.get("/metrics", **extra)
    assert r.status_code == 401 and r["WWW-Authenticate"].startswith("Bearer")


def test_con_el_token_responde_en_formato_prometheus(client, con_token):
    client.get("/api/v1/planes")
    r = client.get("/metrics", HTTP_AUTHORIZATION=f"Bearer {TOKEN}")
    assert r.status_code == 200 and r["Content-Type"].startswith("text/plain")
    assert b"http_server_request_duration_seconds" in r.content


def test_solo_acepta_get(client, con_token):
    assert client.post("/metrics", HTTP_AUTHORIZATION=f"Bearer {TOKEN}").status_code == 405
