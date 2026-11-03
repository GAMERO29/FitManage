"""Regla de oro de la Guía 13: ningún dato personal en claro en un log, una métrica o una traza."""

import logging

from infraestructura.observabilidad.logs import FiltroPII, FormateadorJSON
from infraestructura.observabilidad.privacidad import redactar, seudonimo


def test_el_seudonimo_es_estable_y_no_contiene_el_documento():
    uno = seudonimo("CC", "1090123456")
    assert uno == seudonimo("CC", "1090123456")
    assert len(uno) == 12 and "1090123456" not in uno and "3456" not in uno


def test_el_seudonimo_cambia_con_el_tipo_y_con_la_clave(settings):
    cc = seudonimo("CC", "25789456")
    assert cc != seudonimo("PPT", "25789456")
    settings.SECRET_KEY = "otra-clave-de-otro-despliegue"
    assert cc != seudonimo("CC", "25789456")


def test_el_seudonimo_de_telemetria_no_es_la_huella_que_recibe_el_celular():
    from dominio.modelos import TipoDocumento
    from infraestructura.api.presentacion import huella_documento

    assert seudonimo("CC", "1090123456") not in huella_documento(TipoDocumento.CC, "1090123456")


def test_redactar_quita_el_documento_de_la_ruta_y_las_cifras_largas():
    texto = "Not Found: /api/v1/estados/CC/1090123456 tel 3000000005 desde 10.0.0.7"
    limpio = redactar(texto)
    assert "1090123456" not in limpio and "3000000005" not in limpio
    assert "/api/v1/estados/{tipoDocumento}/{numeroDocumento}" in limpio
    assert "10.0.0.7" in limpio  # una IP corta no es un documento


def _registro(mensaje: str, *args, **extra) -> logging.LogRecord:
    registro = logging.LogRecord("prueba", logging.WARNING, __file__, 1, mensaje, args, None)
    registro.__dict__.update(extra)
    return registro


def test_el_filtro_redacta_el_mensaje_y_sus_argumentos():
    registro = _registro("Not Found: %s", "/api/v1/estados/PPT/25789456")
    assert FiltroPII().filter(registro) is True
    assert "25789456" not in registro.getMessage()


def test_el_json_solo_lleva_los_campos_permitidos():
    import json

    registro = _registro("consulta", evento="consulta_estado", ruta="/x", cedula="1090123456")
    linea = json.loads(FormateadorJSON().format(registro))
    assert linea["evento"] == "consulta_estado" and linea["ruta"] == "/x"
    assert linea["nivel"] == "WARNING" and linea["mensaje"] == "consulta"
    assert "cedula" not in linea and "1090123456" not in json.dumps(linea)


def test_el_json_redacta_las_excepciones():
    import json
    import sys

    try:
        raise ValueError("documento 1090123456 inválido")
    except ValueError:
        registro = logging.LogRecord("x", logging.ERROR, __file__, 1, "falló", (), sys.exc_info())
    linea = json.loads(FormateadorJSON().format(registro))
    assert "ValueError" in linea["excepcion"] and "1090123456" not in linea["excepcion"]
