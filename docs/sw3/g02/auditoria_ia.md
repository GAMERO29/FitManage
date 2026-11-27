# Guía 02 · Auditoría del diagrama de despliegue propuesto por la IA

**Herramienta:** Claude (Anthropic), 27/11/2026, en la misma sesión que resolvió la guía. Esa es una limitación: generó y auditó el mismo asistente. La verificación se apoya en archivos del repositorio, no en lo que el asistente recordaba.

**Prompt:** «Con este inventario, sin credenciales: imagen Docker publicada en GHCR, gunicorn con Django, PostgreSQL 16 gestionado, Render como plataforma, Grafana Cloud para observabilidad, GitHub Actions para CI/CD. Dibuja el diagrama de despliegue con nodos, instancias, enlaces y protocolos en Mermaid.»

**Salida conservada:** `vista_fisica_propuesta_ia.mmd` (y `.png`).

| Afirmación del diagrama | Cómo la comprobé | Resultado |
| --- | --- | --- |
| La página `app.js` la sirve el mismo contenedor | `config/urls.py` (`recepcion/<str:nombre>`) e `infraestructura/web/vistas.py` | Coincide: no hay CDN ni servidor estático aparte. |
| gunicorn con 1 proceso y 4 hilos, usuario 10001 | `docker/arrancar.sh` (línea `exec gunicorn … --workers 1 --threads 4`) y `Dockerfile` (`USER 10001`) | Coincide. |
| La aplicación **envía** trazas y métricas por OTLP a Grafana Cloud | `infraestructura/observabilidad/telemetria.py`: las métricas usan `PrometheusMetricReader` y se publican en `/metrics`; el exportador OTLP de trazas solo se activa si existe `OTEL_EXPORTER_OTLP_ENDPOINT`. El ADR N.° 13 dice que las trazas de producción todavía no van a Grafana Cloud. | **No coincide.** El enlace es al revés y lleva otra cosa: Grafana Cloud **lee** `/metrics` en formato Prometheus. Corregido en `vista_fisica.mmd`. |
| Base gratuita sin respaldos | DT-18 en `docs/deuda-tecnica.md` | Coincide. |
| Una instancia del servicio web | No es observable en el repositorio: es un ajuste del panel de Render. | Se deja con esa fuente declarada; no se puede comprobar desde aquí. |

**Corrección:** el enlace inferido «contenedor → Grafana Cloud por OTLP» se reemplazó por «Grafana Cloud → `/metrics`», y el nodo de Grafana Cloud dice ahora que las trazas OTLP aún no se envían.
