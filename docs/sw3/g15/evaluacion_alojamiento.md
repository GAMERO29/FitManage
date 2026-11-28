# Evaluación de alojamiento del MVP · Guía 15

Versión evaluada: `2bd5e62`, la misma que está desplegada en Render (corrida 46081099053 del workflow *Despliegue*). Precios consultados el 27/11/2026. Todo lo que no tiene fuente está rotulado como **estimación pedagógica**.

## 1. Características NIST aplicadas

Definiciones de NIST SP 800-145, sección 2, *Essential Characteristics*.

| Característica | Capacidad observable en FitManage | Render (hoy) | VM de capacidad fija con cambios por solicitud |
| --- | --- | --- | --- |
| Autoservicio bajo demanda | Crear o cambiar el servicio y la base desde el panel, sin hablar con nadie | Sí. El servicio y la base se crearon desde el panel en la Software II, y los despliegues los dispara un hook sin intervención humana. | No. Cada cambio espera a que alguien atienda la solicitud. |
| Acceso amplio por red | `/api/v1/salud` responde por HTTPS desde el PC de recepción y desde un celular | Sí | Sí. Por eso el acceso remoto, por sí solo, no prueba que algo sea nube. |
| Agrupación de recursos | El servicio comparte hardware con otros clientes y solo se elige la región, no el servidor | Sí. El plan de 0,5 CPU es una fracción de una máquina compartida. | Depende del proveedor. Si es un servidor dedicado, no. |
| Elasticidad rápida | Cambiar el tipo o el número de instancias y ver el cambio de capacidad con la misma carga | **Parcial.** El tipo de instancia se cambia en el panel. El autoescalado exige el workspace Pro (US$25 al mes) y una instancia gratuita no escala. No se ha observado. | No |
| Servicio medido | Ver horas de instancia, GB transferidos y almacenamiento, y que el cobro salga de eso | Sí. El panel cuenta las 750 horas gratuitas, el ancho de banda y el almacenamiento. | No. Es una tarifa fija. |

**Conclusión.** Una VM de capacidad fija con cambios por solicitud cumple el acceso por red y, a lo sumo, la agrupación de recursos. No cumple autoservicio, elasticidad ni servicio medido. Es alojamiento remoto, no nube en el sentido de NIST.

## 2. Objetivos de calidad y recuperación del MVP

| Objetivo | Valor | Por qué ese valor |
| --- | --- | --- |
| Respuesta de la consulta de estado | p95 < 2 s (QA-01 y RNF-01); alarma de ingeniería en 300 ms (ADR N.° 08) | La recepcionista consulta con el socio frente al mostrador. |
| **RTO** | **4 h** dentro del horario del gimnasio (5:00 a. m. a 10:00 p. m.) | El plan B en papel del runbook aguanta medio turno. Más de 4 h de entradas en hoja se vuelven difíciles de pasar al sistema el mismo día. |
| **RPO** | **24 h** | Lo que se pierda se reconstruye con los comprobantes de pago del día y la hoja de entradas. |

## 3. Alternativas y costo mensual

Misma carga para las dos alternativas: un gimnasio con 1 o 2 recepcionistas, 200 consultas y 30 pagos al día como **estimación pedagógica**, y 2.000 socios y 20.000 pagos de datos, que es el tamaño de QA-01. La base de carga ocupa 13 MB en disco.

**Transferencia medida.** En la prueba nominal, cada consulta de estado bajó en promedio 335 bytes, contando cabeceras (104.726 bytes recibidos en 313 peticiones). La interfaz completa (`infraestructura/web/`, con HTML, CSS, JS y las dos fuentes) pesa 168.509 bytes sin comprimir. Con 20 cargas completas al día, que es el peor caso porque no cuenta la caché del navegador, más 230 llamadas a la API de 1 KB, la salida mensual es de unos **0,11 GB**.

### A. Local: un mini PC en la recepción como servidor

| Rubro | Supuesto | COP al mes | Origen |
| --- | --- | --- | --- |
| Equipo | Mini PC reacondicionado de COP 900.000 a 36 meses | 25.000 | Estimación pedagógica |
| Energía | 15 W promedio × 24 h × 30 días = 10,8 kWh, a 1.042,74 COP/kWh (costo unitario de CENS de 868,95 COP/kWh en el III trimestre de 2025, más la contribución del 20 % de los usuarios comerciales) | 11.262 | Superservicios, *Boletín tarifario de energía, III trimestre de 2025*, tabla 13 |
| Respaldo | Disco USB de 1 TB de COP 220.000 a 36 meses, con un `pg_dump` cada noche | 6.111 | Estimación pedagógica |
| UPS pequeña | COP 250.000 a 36 meses | 6.944 | Estimación pedagógica |
| Transferencia | No sale a internet si solo se usa en la sede | 0 | — |
| **Total** | | **≈ 49.300** | Sin contar las horas de parches y soporte, que serían del equipo |

### B. Nube: Render en planes pagos mínimos

| Rubro | Supuesto | US$ al mes | Origen |
| --- | --- | --- | --- |
| Workspace | Hobby: 1 miembro, 5 GB de salida incluidos | 0 | render.com/pricing |
| Servicio web | 0.5c-512mb, siempre despierto | 7,00 | render.com/pricing |
| Base | Render Postgres 0.1c-256mb, con PITR de 3 días | 6,00 | render.com/pricing y docs/postgresql-backups |
| Almacenamiento | 1 GB a US$0,30 | 0,30 | render.com/pricing |
| Transferencia | 0,11 GB medidos, frente a 5 GB incluidos | 0 | Medición propia y render.com/pricing |
| **Total** | | **13,30 ≈ COP 44.000** | TRM de COP 3.309,55 del 18/11/2026 (Portafolio) |

**B0, lo que hay hoy (plan Free): US$0.** No es una alternativa válida. La base vence el 2/12/2026 y no tiene ningún respaldo, así que el RPO es infinito. El servicio web se duerme tras 15 minutos sin tráfico, de modo que el primer socio de las 5:00 a. m. espera cerca de un minuto.

### Comparación con los objetivos

| Alternativa | Costo | RPO | RTO | Riesgo principal |
| --- | --- | --- | --- | --- |
| A. Local | ≈ COP 49.300 | 24 h, si el `pg_dump` nocturno corre todos los días | Si se daña el equipo, conseguir otro toma de 1 a 3 días: **no cumple** sin un equipo de repuesto | El trabajo de operación cae en una sola persona; los cortes de luz |
| B. Render pago | ≈ COP 44.000 | Minutos (PITR de 3 días) | Hipótesis: menos de 1 h para restaurar en una base nueva. Se prueba en la Guía 16. | Depende de que la sede tenga internet |
| B0. Render Free | 0 | **Ninguno**: no hay respaldos | No aplica después del vencimiento | Pérdida total de datos el 2/12/2026 más 14 días |

## 4. Pruebas de carga en el laboratorio

Ambiente: contenedor Linux con 2 núcleos y 8.023 MB de RAM, PostgreSQL 16 con la base `fitmanage_carga` (2.000 socios y 20.000 pagos), gunicorn con 2 procesos y k6 en la misma máquina. No es producción y no hay red de por medio.

| Condición | Volumen | Tiempo de medición | p95 | Mediana | Máximo | Errores | Umbrales |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nominal: 2 usuarios simultáneos | 313 peticiones (1,73/s) | 3 min, desde las 19:36 | 11,8 ms | 7,5 ms | 654 ms | 0 % | Todos pasan |
| Mayor demanda: QA-01, 10 usuarios simultáneos | 5.385 peticiones (8,96/s) | 10 min, desde las 19:39 | 11,9 ms | 7,7 ms | 144 ms | 0 % | Todos pasan |

Evidencia: `nominal-salida-k6.txt`, `qa01-salida-k6.txt` y sus resúmenes JSON, sin el token de `setup_data`.

**Lectura honesta.** Con 5 veces la carga, el p95 pasó de 11,8 a 11,9 ms. Eso dice que, con este volumen de datos, la consulta no está limitada por capacidad en el laboratorio. No dice nada sobre elasticidad, porque la capacidad fue la misma en las dos corridas. El máximo de la corrida nominal, 654 ms, fue una consulta aislada: el p90 fue de 10,0 ms. No investigué su causa, y no cambia la lectura frente al umbral de 2 s.

**Supuestos que faltan para justificar elasticidad o mayor disponibilidad:**

1. **Hardware equivalente.** El laboratorio tiene 2 núcleos. El plan de Render tiene 0,5 CPU y 512 MB, así que hay que repetir la carga contra un servicio de Render con ese plan. Contra producción no se puede, por la regla de la Guía 8, así que haría falta un servicio aparte.
2. **Red real.** Falta la latencia desde la sede del gimnasio hasta Render, que el laboratorio no incluye.
3. **Elasticidad observada.** Haría falta el workspace Pro, el autoescalado activo y la misma carga antes y después, viendo el cambio en instancias y en p95.
4. **Disponibilidad.** Haría falta el SLI del ADR N.° 14 durante 14 días con la base en plan pago, y un registro de caídas del internet de la sede durante el mismo periodo.
