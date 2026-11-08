"""Ejercicio 3 de la Guía 13: el endpoint crítico (QA-01) emite span, métricas y log JSON."""

import json
import logging

import pytest
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.sampling import ParentBased
from prometheus_client import REGISTRY, generate_latest

from infraestructura.observabilidad import telemetria
from infraestructura.observabilidad.logs import FiltroPII, FormateadorJSON
from infraestructura.observabilidad.privacidad import seudonimo

RUTA = "/api/v1/estados/{tipoDocumento}/{numeroDocumento}"


@pytest.fixture
def spans(monkeypatch):
    """Todo se muestrea en las pruebas; en producción, el 10 % (ADR N.° 13)."""
    proveedor = telemetria.configurar()
    memoria = InMemorySpanExporter()
    procesador = SimpleSpanProcessor(memoria)
    proveedor.add_span_processor(procesador)
    monkeypatch.setattr(telemetria, "muestrear_todo", True)
    yield memoria
    procesador.shutdown()


@pytest.fixture
def lineas():
    """Captura lo que el handler de producción escribiría, con su formateador y su filtro."""
    import io

    salida = io.StringIO()
    handler = logging.StreamHandler(salida)
    handler.setFormatter(FormateadorJSON())
    handler.addFilter(FiltroPII())
    raiz = logging.getLogger()
    raiz.addHandler(handler)
    yield lambda: [json.loads(x) for x in salida.getvalue().splitlines() if x]
    raiz.removeHandler(handler)


@pytest.fixture
def recepcion(api):
    return api.como("laura@gimnasio-demo.co")


def _metricas() -> str:
    return generate_latest(REGISTRY).decode()


def test_la_consulta_deja_un_span_con_la_ruta_y_no_con_el_documento(recepcion, spans):
    recepcion.get("/api/v1/estados/CC/1090123456")
    por_nombre = {s.name: s for s in spans.get_finished_spans()}
    http = por_nombre[f"GET {RUTA}"]
    assert http.attributes["http.route"] == RUTA
    assert http.attributes["http.response.status_code"] == 200
    hijo = por_nombre["consultar_estado"]
    assert hijo.parent.span_id == http.context.span_id
    assert hijo.attributes["fitmanage.resultado"] == "ACTIVO"
    assert hijo.attributes["fitmanage.socio.seudonimo"] == seudonimo("CC", "1090123456")
    terminados = spans.get_finished_spans()
    todo = json.dumps([dict(s.attributes) for s in terminados] + [s.name for s in terminados])
    assert "1090123456" not in todo and "3000000005" not in todo


def test_un_documento_inexistente_tambien_queda_seudonimizado(recepcion, spans, lineas):
    recepcion.get("/api/v1/estados/CC/1111111111")
    hijo = next(s for s in spans.get_finished_spans() if s.name == "consultar_estado")
    assert hijo.attributes["fitmanage.resultado"] == "NO_ENCONTRADO"
    texto = json.dumps(lineas())
    assert "1111111111" not in texto


def test_la_consulta_escribe_un_log_json_correlacionado_con_la_traza(recepcion, spans, lineas):
    recepcion.get("/api/v1/estados/CC/1093445566")
    eventos = {linea["evento"]: linea for linea in lineas() if "evento" in linea}
    consulta, peticion = eventos["consulta_estado"], eventos["peticion"]
    assert consulta["resultado"] == "VENCIDO"
    assert consulta["seudonimo"] == seudonimo("CC", "1093445566")
    assert peticion["ruta"] == RUTA and peticion["estado"] == 200 and peticion["duracion_ms"] >= 0
    http = next(s for s in spans.get_finished_spans() if s.name.startswith("GET "))
    assert peticion["trace_id"] == consulta["trace_id"] == format(http.context.trace_id, "032x")
    assert "1093445566" not in json.dumps(eventos)


def test_las_metricas_cuentan_peticiones_latencia_y_resultados(recepcion, spans):
    recepcion.get("/api/v1/estados/CC/1090123456")
    recepcion.get("/api/v1/estados/TI/1090123456")
    texto = _metricas()
    assert "http_server_request_duration_seconds_bucket" in texto
    assert 'http_route="/api/v1/estados/{tipoDocumento}/{numeroDocumento}"' in texto
    assert 'http_response_status_code="400"' in texto
    assert "fitmanage_consultas_estado_total{" in texto and 'resultado="ACTIVO"' in texto
    assert "1090123456" not in texto


def test_una_ruta_que_no_existe_no_crea_una_serie_por_url(client, spans):
    client.get("/api/v1/estados/CC/1090123456/extra/9988776655")
    assert "9988776655" not in _metricas()
    assert 'http_route="sin_ruta"' in _metricas()


def test_la_pantalla_de_recepcion_se_etiqueta_como_la_raiz(client, spans):
    client.get("/")
    assert 'http_route="/"' in _metricas()


def test_la_salud_y_las_metricas_no_cuentan_como_trafico(client, spans):
    client.get("/api/v1/salud")
    assert not [s for s in spans.get_finished_spans() if "salud" in s.name]


@pytest.mark.parametrize(
    ("valor", "esperada"),
    [(None, 0.1), ("0.2", 0.2), ("1", 1.0), ("0", 0.0), ("2", 0.1), ("-1", 0.1), ("diez", 0.1)],
)
def test_la_tasa_de_muestreo_es_un_10_por_ciento_salvo_un_valor_valido(valor, esperada):
    assert telemetria.proporcion_muestreo(valor) == esperada


def test_el_muestreo_respeta_la_decision_de_quien_llama(monkeypatch):
    monkeypatch.setattr(telemetria, "proporcion", 0.1)
    muestreador = telemetria.muestreador()
    assert isinstance(muestreador, ParentBased)
    assert "0.1" in muestreador.get_description()


def test_configurar_dos_veces_devuelve_el_mismo_proveedor():
    assert telemetria.configurar() is telemetria.configurar()


def test_sin_muestrear_igual_hay_trace_id_para_correlacionar_logs(recepcion, lineas, monkeypatch):
    telemetria.configurar()
    monkeypatch.setattr(telemetria, "muestrear_todo", False)
    monkeypatch.setattr(telemetria, "proporcion", 0.0)
    recepcion.get("/api/v1/estados/CC/1090123456")
    peticion = next(x for x in lineas() if x.get("evento") == "peticion")
    assert len(peticion["trace_id"]) == 32 and peticion["muestreada"] is False


def test_produccion_no_usa_el_access_log_de_gunicorn():
    """El access log escribía «GET /api/v1/estados/CC/1098765432» en los logs de Render."""
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[2]
    for archivo in ("Dockerfile", "docker/arrancar.sh"):
        codigo = [
            x
            for x in (raiz / archivo).read_text(encoding="utf-8").splitlines()
            if not x.lstrip().startswith("#")
        ]
        assert not [x for x in codigo if "--access-logfile" in x]


def test_django_registra_la_configuracion_de_logs_en_json(settings):
    manejador = settings.LOGGING["handlers"]["json"]
    assert settings.LOGGING["formatters"]["json"]["()"].endswith("FormateadorJSON")
    assert "pii" in manejador["filters"]


def test_sin_colector_las_trazas_no_se_exportan(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    assert telemetria.procesador_de_exportacion() is None


def test_con_colector_las_trazas_salen_por_otlp(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4318")
    procesador = telemetria.procesador_de_exportacion()
    assert type(procesador.span_exporter).__name__ == "OTLPSpanExporter"
    procesador.shutdown()
