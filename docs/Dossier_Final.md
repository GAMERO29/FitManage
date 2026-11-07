# Dossier Técnico Final · FitManage

Ingeniería de Software I y II · Universidad de Pamplona · Juan Sebastián Cárdenas Acevedo · Cierre: 6/11/2026 (FPI-32).

Regla de este documento: cada afirmación lleva al lugar donde se puede comprobar. Lo que no se pudo comprobar se dice.

## 1. Ficha técnica

| | |
| --- | --- |
| Problema (FPI-01) | En hora pico, la recepción de un gimnasio de barrio no sabe si la persona que llega pagó, y la fila crece. FitManage responde eso por documento, en segundos. |
| Sistema en producción | https://fitmanage-svol.onrender.com (pantalla de recepción en `/`, API en `/api/v1`) |
| Repositorio | https://github.com/GAMERO29/FitManage · release **v1.0.0** |
| Video demo | Pendiente de grabación; guion en [`docs/demo/guion-video.md`](demo/guion-video.md). |
| Stack | Django 5.2 LTS, Python 3.12, PostgreSQL 16, gunicorn, OpenTelemetry, imagen en `ghcr.io/gamero29/fitmanage`, Render (plan gratuito). |

## 2. Verificación y validación

**Verificación (¿lo construimos bien?).** Tiene evidencia fuerte: la suite completa corre en cada PR, con cobertura de 99 % (`docs/guia-15-sw2/evidencia/pruebas-rama.txt`); el contrato OpenAPI se valida en cada respuesta y con Pact; QA-01 dio un p95 de 13,5 ms con 10 usuarios (`docs/pruebas/carga/qa01-con-adr08-resumen.json`); QA-05 resistió 100 pares de pagos concurrentes; el último despliegue pasó el healthcheck 3/3 (corrida 42329845440 del workflow `Despliegue`).

**Validación (¿construimos lo correcto?).** Es la parte débil, y se dice:

- Hasta la Guía 16 **no existía una pantalla que recepción pudiera usar**: solo la API. Se construyó en esta guía (ADR N.° 16).
- **Ningún usuario real ha usado el sistema.** Las reglas de negocio salen de la entrevista y la observación de Software I (FPI-04), pero no hubo piloto.
- **No se pueden cargar socios reales** hasta tener el aviso de privacidad aprobado (DT-10, hito H2).

## 3. Línea de tiempo de Ingeniería de Software II (FPI-17 a FPI-31)

| Ficha | Decisión clave | ¿Se mantuvo? | Estado final |
| --- | --- | --- | --- |
| FPI-17 | Línea base LB-1 y puerta de calidad automática (ADR 01). | Se mantuvo y creció: de un flujo `Calidad` a nueve checks. | Vigente. |
| FPI-18 | Drivers priorizados: integridad del pago, consulta en hora pico, sin conexión, costo 0 (ADR 02). | Se mantuvo. | Vigente; QA-02 sin conexión sigue pendiente (H4). |
| FPI-19 | Una sola aplicación Django con plantillas (ADR 03). | **Cambió en parte:** las plantillas nunca se construyeron. | Reemplazado en la interfaz por el ADR 16. |
| FPI-20 | Monolito modular con núcleo hexagonal donde hay dinero (ADR 04). | Se mantuvo; la Guía 15 corrigió una desviación (DT-16). | Vigente. |
| FPI-21 | No distribuir ningún contexto (ADR 05). | Se mantuvo. | Vigente; defendido en la sección 4. |
| FPI-22 | JWT de 15 min y renovación en cookie `HttpOnly` (ADR 06). | Se mantuvo; la pantalla de recepción lo usa. | Vigente. |
| FPI-23 | Pirámide de pruebas con base real y dobles solo en las fronteras (ADR 07). | Se mantuvo. | Vigente. |
| FPI-24 | k6 contra un entorno local; conexiones persistentes, sin caché (ADR 08). | Se mantuvo. | Vigente. |
| FPI-25 | El pipeline CI es la única puerta a `main` (ADR 09). | Se mantuvo y se amplió a nueve checks. | Vigente. |
| FPI-26 | Imagen multietapa sin root (ADR 10). | Se mantuvo. | Vigente. |
| FPI-27 | CD a Render con healthcheck y rollback a `estable` (ADR 11). | Se mantuvo; un despliegue manual volvió a una imagen vieja y se corrigió. | Vigente. |
| FPI-28 | Semgrep y Trivy bloquean críticos y altos; excepciones con vencimiento (ADR 12). | Se mantuvo; en la Guía 16 se sumó la puerta de licencias. | Vigente. |
| FPI-29 | OpenTelemetry al 10 % y logs sin datos personales (ADR 13). | Se mantuvo. | Vigente. |
| FPI-30 | SLO de 99,5 % en 14 días con alertas por consumo (ADR 14). | Se mantuvo; el SLI pasó a cubrir el recorrido completo tras el postmortem. | Vigente. |
| FPI-31 | Pagar DT-16, convivir con DT-04/06/12, Django 5.2 LTS (ADR 15). | Se mantuvo; H0 se cumplió el 6/11. | Vigente. |

## 4. Defensa de decisiones con evidencia

| ADR | Decisión | Evidencia |
| --- | --- | --- |
| 05 | No distribuir en microservicios. | Con 10 recepcionistas simultáneas, un solo proceso responde con p95 de **13,5 ms** y 0 errores; con 50, **37,8 ms** (`docs/pruebas/carga/`). El límite de RNF-01 es 2 s: hay más de 50 veces de margen. Distribuir costaría unos **94 USD al mes** (`docs/guia-05-sw2/costos.py`) y no arregla la falla que sí ocurrió: en los dos simulacros, lo que se cayó fue la base de datos (postmortem del 6/11/2026). Con una base por servicio habría más bases que pueden caerse. |
| 14 | SLO de 99,5 % y no de 99,9 %. | Un simulacro de 30 minutos sin base consumió el **30 %** del presupuesto de 14 días. Con 99,9 % ese mismo incidente habría agotado el presupuesto. La alerta rápida avisó a los 2 minutos y no se apagó antes de tiempo (corrida 42312082387). |
| 13 | Trazas al 10 %. | Medido: el 100 % sube la CPU un 9,7 % frente a un 5,8 % con el 10 %, sin cambiar la latencia (`docs/guia-13-sw2/evidencia/costo-telemetria.md`). Ningún documento de socio aparece en logs, métricas ni trazas: el workflow `Observabilidad` falla si encuentra uno. |
| 12 | La seguridad bloquea el pipeline. | Los PR de la Guía 16 pasaron `sast`, `sca-dependencias`, `sca-imagen` y `secretos`; las 12 excepciones de `.trivyignore` tienen razón y vencen el 1/2/2027. |

## 5. Estado verificable en vivo

| Indicador | Estado real | Dónde se comprueba |
| --- | --- | --- |
| Producción | Viva: healthcheck 3/3 y `/api/v1/estados` exige token (401). | Workflow `Despliegue`, corrida 42329845440 (6/11/2026). |
| Cobertura | 99 % (líneas y ramas). | Job `pruebas` de cada PR. |
| Quality Gate de SonarCloud | Aprobado en `main`; 0 *hotspots*; 1 issue nueva abierta. | Check «SonarCloud Code Analysis». |
| Vulnerabilidades críticas o altas sin mitigar | 0: si hubiera una, los checks `sca-*` fallarían. | Checks requeridos de cada PR. |
| Licencias | 49 dependencias de ejecución: MIT, BSD, Apache-2.0, PSF, LGPL-3.0 (psycopg) y MPL-2.0 (certifi). Ninguna GPL ni AGPL. | `docs/guia-16-sw2/evidencia/licencias-dependencias.md` y el check `sca-dependencias`. |
| SLO de producción | No verificado desde aquí: Grafana Cloud no es accesible desde este entorno. | Captura del tablero (FPI-32, sección E). |

## 6. Auditoría ética de IA

Consolidada en [`docs/guia-16-sw2/bitacora-ia.md`](guia-16-sw2/bitacora-ia.md): las 31 fichas, 16 alucinaciones comprobadas en 14 fichas, 30 dependencias o herramientas rechazadas, 0 licencias restrictivas, 7 propuestas con secretos en claro y 2 fugas de datos personales prevenidas. FitManage se construyó además con un asistente de IA en modo de programación en pareja; cada cambio pasó por PR con los checks requeridos, y las decisiones quedaron en los ADR.

## 7. Deuda residual aceptada

Inventario completo en [`docs/deuda-tecnica.md`](deuda-tecnica.md) y plan en [`docs/roadmap.md`](roadmap.md). Las que más pesan:

| Componente | Tipo | Justificación y plan |
| --- | --- | --- |
| Base de Render gratuita (DT-18) | Infraestructura | Costo 0 mientras no hay datos reales. Vence cerca del 2/12/2026: plan de US$6 o exportación, hito H1. |
| Aviso de privacidad (DT-10) y auditoría (DT-14) | Cumplimiento | Sin datos reales todavía. Se paga antes del primer socio real, hito H2. |
| Gestión de planes y personal (DT-24) | Funcionalidad | La operación de la demo no la necesita. Hito H2. |
| Prototipo con reglas propias (DT-04, DT-06) | Diseño | Se convive: no se despliega (ADR 15). |
