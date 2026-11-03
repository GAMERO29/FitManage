"""Cliente del Deploy Hook de Render: nunca imprime el hook y solo despliega nuestra imagen."""

from __future__ import annotations

import urllib.error

import pytest

from despliegue import render

HOOK = "https://api.render.com/deploy/srv-abc123?key=SECRETO-NO-IMPRIMIR"
IMAGEN = "ghcr.io/gamero29/fitmanage:sha-29860b3f6ad0e6dfdbe85ba6c48eeefd36cea5c0"


class Respuesta:
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_agrega_la_imagen_codificada_al_hook():
    url = render.url_de_despliegue(HOOK, IMAGEN)
    assert url.startswith(HOOK + "&imgURL=ghcr.io%2Fgamero29%2Ffitmanage%3Asha-29860b3")


@pytest.mark.parametrize(
    ("hook", "imagen"),
    [
        ("http://api.render.com/deploy/srv-abc?key=x", IMAGEN),
        ("https://otro-sitio.com/deploy/srv-abc?key=x", IMAGEN),
        (HOOK, "docker.io/library/python:3.12"),
    ],
    ids=["sin-https", "otro-dominio", "otra-imagen"],
)
def test_rechaza_hooks_o_imagenes_ajenas(hook, imagen):
    with pytest.raises(ValueError):
        render.url_de_despliegue(hook, imagen)


def test_despliegue_aceptado(capsys):
    pedidas = []

    def abrir(peticion, timeout):
        pedidas.append(peticion)
        return Respuesta()

    assert render.desplegar(IMAGEN, HOOK, abrir) == 0
    assert pedidas[0].get_method() == "POST"
    assert "SECRETO" not in capsys.readouterr().out


@pytest.mark.parametrize(
    "error",
    [
        urllib.error.HTTPError(HOOK, 401, "Unauthorized", {}, None),
        urllib.error.URLError("sin red"),
    ],
    ids=["rechazado", "sin-red"],
)
def test_si_render_falla_no_imprime_el_hook(error, capsys):
    def abrir(peticion, timeout):
        raise error

    assert render.desplegar(IMAGEN, HOOK, abrir) == 1
    assert "SECRETO" not in capsys.readouterr().out


def test_main_sin_hook_o_con_imagen_ajena(monkeypatch, capsys):
    monkeypatch.delenv("HOOK", raising=False)
    monkeypatch.delenv("RENDER_DEPLOY_HOOK", raising=False)
    assert render.main([IMAGEN]) == 2
    monkeypatch.setenv("RENDER_DEPLOY_HOOK", HOOK)
    assert render.main(["docker.io/otra:1"]) == 2
    assert "SECRETO" not in capsys.readouterr().out


def test_main_despliega(monkeypatch):
    monkeypatch.setenv("HOOK", HOOK)
    monkeypatch.setattr(render, "desplegar", lambda imagen, hook: 0)
    assert render.main([IMAGEN]) == 0
