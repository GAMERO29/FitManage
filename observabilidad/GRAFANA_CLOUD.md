# Tablero de producción en Grafana Cloud (plan gratuito)

Render no puede correr Prometheus, así que en producción lo hace Grafana Cloud (conectado el 6/11/2026): su integración **Metrics Endpoint** lee `https://fitmanage-svol.onrender.com/metrics` cada minuto con un token, y el tablero es el mismo que el de compose (`observabilidad/grafana/provisioning/dashboards/fitmanage.json`).

1. **Token de métricas.** Generarlo en la propia máquina (`openssl rand -hex 32`) y guardarlo en un gestor de contraseñas. Nunca en el repositorio ni en un chat.
2. **Render.** En el servicio, *Environment*, agregar `FITMANAGE_METRICAS_TOKEN` con ese valor y guardar. Render redespliega solo. Sin el token, `/metrics` responde 404; con el token y sin credenciales, 401.
3. **Grafana Cloud.** En el stack: *Connections* → *Metrics Endpoint*. Crear el scrape job con nombre `fitmanage`, URL `https://fitmanage-svol.onrender.com/metrics`, intervalo de 1 minuto y autenticación *Bearer* con el token (sin la palabra «Bearer»). Probar la conexión y guardar.
**Image URL en Render.** Debe ser `ghcr.io/gamero29/fitmanage:estable`, no una etiqueta `sha-…` fija: el botón *Manual Deploy* de Render usa esa dirección, y con una imagen vieja (anterior a `/app/arrancar.sh`) el contenedor termina con estado 128 sin escribir logs.

4. **Tablero.** *Dashboards* → *New* → *Import*, subir `fitmanage.json` y elegir la fuente de datos Prometheus del stack (la que termina en `-prom`) en el selector «Fuente de datos».
5. **Destino de las alertas.** En *Alerting* → *Notification configuration* → *Contact points*, el destino que usa la política por defecto puede venir vacío («empty», sin integraciones). Editarlo, agregar la integración *Email* con el correo propio, probarlo con *Test* y guardarlo.
6. **Alertas.** El Prometheus de Grafana Cloud no lee `observabilidad/prometheus/alertas.yml`; las dos reglas se crean en *Alerting* → *Alert rules* con los mismos umbrales, pero con ventanas de `[5m]` en lugar de `[1m]`: con una lectura por minuto, `rate(...[1m])` no tiene dos muestras y queda vacío. Los paneles del tablero ya usan `$__rate_interval`, que Grafana ajusta solo al intervalo de lectura. En las dos reglas, *Alert state if no data* va en **Normal**: sin 5xx o de noche, sin consultas, la consulta queda vacía y eso no es un incidente. Evaluación cada 1 minuto en el grupo `fitmanage-api`, con 2 minutos de espera para los errores y 5 para la latencia.

Efecto en Render: una lectura por minuto mantiene despierta la instancia gratuita, que deja de dormirse a los 15 minutos. Render da 750 horas gratis al mes por workspace y un mes despierto son unas 744, así que alcanza para este único servicio.

Trazas (opcional): Grafana Cloud recibe OTLP. Con `OTEL_EXPORTER_OTLP_ENDPOINT` y `OTEL_EXPORTER_OTLP_HEADERS` (los valores salen de *Connections* → *OpenTelemetry (OTLP)* del stack) en Render, el 10 % muestreado de las trazas va a Tempo.

## SLO (Guía 14, ADR N.° 14)

En compose, las alertas de umbral se reemplazaron por las de consumo del presupuesto de `observabilidad/prometheus/slo.yml`. En Grafana Cloud siguen las dos de umbral, creadas a mano; para pasarlas al SLO hay que crear `PresupuestoQuemaRapida` y `PresupuestoQuemaLenta` con las expresiones de `slo.yml` (sin las reglas de registro, escribiendo la proporción completa) y ventanas de al menos `[5m]`. La fila «SLO del recorrido de recepción» del tablero ya funciona allá si se vuelve a importar `fitmanage.json`.
