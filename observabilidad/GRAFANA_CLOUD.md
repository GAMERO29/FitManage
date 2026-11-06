# Tablero de producción en Grafana Cloud (plan gratuito)

Render no puede correr Prometheus, así que en producción lo hace Grafana Cloud: su integración **Metrics Endpoint** lee `https://fitmanage-svol.onrender.com/metrics` cada minuto con un token, y el tablero es el mismo que el de compose (`observabilidad/grafana/provisioning/dashboards/fitmanage.json`).

1. **Token de métricas.** Generarlo en la propia máquina (`openssl rand -hex 32`) y guardarlo en un gestor de contraseñas. Nunca en el repositorio ni en un chat.
2. **Render.** En el servicio, *Environment*, agregar `FITMANAGE_METRICAS_TOKEN` con ese valor y guardar. Render redespliega solo. Sin el token, `/metrics` responde 404; con el token y sin credenciales, 401.
3. **Grafana Cloud.** En el stack: *Connections* → *Metrics Endpoint*. Crear el scrape job con nombre `fitmanage`, URL `https://fitmanage-svol.onrender.com/metrics`, intervalo de 1 minuto y autenticación *Bearer* con el token (sin la palabra «Bearer»). Probar la conexión y guardar.
4. **Tablero.** *Dashboards* → *New* → *Import*, subir `fitmanage.json` y elegir la fuente de datos Prometheus del stack (la que termina en `-prom`) en el selector «Fuente de datos».
5. **Destino de las alertas.** En *Alerting* → *Notification configuration* → *Contact points*, la cuenta nueva trae el destino `empty`, que usa la política por defecto pero no tiene ningún canal. Editarlo, agregar la integración *Email* con el correo del responsable, probarlo con *Test* y guardarlo.
6. **Alertas.** El Prometheus de Grafana Cloud no lee `observabilidad/prometheus/alertas.yml`; las dos reglas se crean en *Alerting* → *Alert rules* con los mismos umbrales, pero con ventanas de `[5m]` en lugar de `[1m]`: con una lectura por minuto, `rate(...[1m])` no tiene dos muestras y queda vacío. Los paneles del tablero ya usan `$__rate_interval`, que Grafana ajusta solo al intervalo de lectura. En las dos reglas, *Alert state if no data* va en **Normal**: sin ningún 5xx, o de noche sin consultas, la expresión queda vacía y no es un error.

Estado actual (6/11/2026): conectado. Stack con el scrape job `fitmanage`, el tablero importado y las reglas `ErroresDelServidor` (umbral 0,05, pendiente 2 min) y `ConsultaDeEstadoLenta` (umbral 0,3 s, pendiente 5 min) en la carpeta `FitManage`, grupo `fitmanage-api`, evaluadas cada minuto.

## Si un despliegue manual falla en Render

El pipeline siempre le indica a Render qué imagen desplegar, pero *Manual Deploy* usa la que está guardada en *Settings* → *Image* → *Source*. Ahí quedó hasta el 6/11/2026 `sha-29860b37…`, la imagen de la Guía 11 sin `/app/arrancar.sh`, y el despliegue manual salía con «Exited with status 128» sin una sola línea de log. Ahora dice `ghcr.io/gamero29/fitmanage:estable`, la etiqueta que el workflow `Despliegue` mueve a la última versión que pasó el healthcheck, así que un despliegue manual nunca vuelve a una imagen vieja.

Efecto en Render: una lectura por minuto mantiene despierta la instancia gratuita, que deja de dormirse a los 15 minutos. Render da 750 horas gratis al mes por workspace y un mes despierto son unas 744, así que alcanza para este único servicio.

Trazas (opcional): Grafana Cloud recibe OTLP. Con `OTEL_EXPORTER_OTLP_ENDPOINT` y `OTEL_EXPORTER_OTLP_HEADERS` (los valores salen de *Connections* → *OpenTelemetry (OTLP)* del stack) en Render, el 10 % muestreado de las trazas va a Tempo.
