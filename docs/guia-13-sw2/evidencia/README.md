# Evidencia de la Guía 13 (FPI-29)

## Workflow `Observabilidad`, corrida 41712539584 (PR #24)

Levanta FitManage con Prometheus, Grafana y Jaeger (`docker compose --profile observabilidad`), siembra el volumen de QA-01, manda 6 minutos de tráfico de recepción con k6 y, desde el minuto 2, apaga la base de datos 2 min 30 s.

| Señal | Valor |
| --- | --- |
| Peticiones atendidas | 1.645 (794 con 200, 96 con 404, 21 con 400 y 715 con 500 durante el apagón) |
| Tasa promedio | 3,9 peticiones por segundo |
| Errores 5xx en la ventana de 7 minutos | 44 % (100 % mientras la base estuvo apagada) |
| Alerta `ErroresDelServidor` | Se disparó durante el apagón |
| Trazas guardadas en Jaeger | 188 de 1.645 peticiones (11,4 %; muestreo configurado en 10 %) |
| Documentos de socios en logs, métricas y trazas | 0 (el workflow falla si encuentra uno) |
| Disco de Prometheus | 60 KB, 90 series |
| Logs JSON de la app | 5,4 MB, unos 3.300 bytes por petición (las de error traen la traza de la excepción) |

Capturas tomadas por el workflow con Chromium:

- [`grafana-apagon.png`](grafana-apagon.png): el tablero durante el apagón, con los errores al 100 % y la alerta activa.
- [`grafana.png`](grafana.png): el tablero al terminar, con la base recuperada.
- [`jaeger.png`](jaeger.png): una traza de la consulta de estado. El socio aparece como `fitmanage.socio.seudonimo`.

## Antes y después en el log de gunicorn

Antes, con `--access-logfile -` (lo que corría en Render hasta esta guía):

```
127.0.0.1 - - [03/Nov/2026:14:19:43 -0500] "GET /api/v1/estados/CC/1098765432 HTTP/1.1" 401 177 "-" "curl/8.5.0"
```

Después, con los logs JSON y el filtro de datos personales, la misma petición sin token:

```
{"momento": "2026-11-03T19:23:50.884+00:00", "nivel": "INFO", "logger": "fitmanage.peticiones", "mensaje": "petición atendida", "trace_id": "2753119393f034114b7d1cc2bd2e73af", "span_id": "03c5912134a3bee9", "evento": "peticion", "metodo": "GET", "ruta": "/api/v1/estados/{tipoDocumento}/{numeroDocumento}", "estado": 401, ...}
{"momento": "2026-11-03T19:23:50.885+00:00", "nivel": "WARNING", "logger": "django.request", "mensaje": "Unauthorized: /api/v1/estados/{tipoDocumento}/{numeroDocumento}"}
```

La segunda línea muestra la otra fuga que apareció al activar los logs: Django escribe la ruta completa en cada 401 y 404. El filtro la redacta.

## Otras evidencias

- [`costo-telemetria.md`](costo-telemetria.md): medición local de latencia, CPU y volumen de logs con la telemetría apagada, al 10 % y al 100 %.
- [`revertir-hash-ia.txt`](revertir-hash-ia.txt): el «hash» de cédula que propuso la IA se revierte en 1,7 segundos.
