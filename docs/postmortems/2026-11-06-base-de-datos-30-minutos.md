# Postmortem · La base de datos dejó de responder 30 minutos y el SLI dio la caída por resuelta antes de tiempo (2026-11-06)

> Sin culpables: se asume que cada persona hizo lo correcto con la información que tenía. Se buscan las fallas del proceso, de las defensas y de la arquitectura que dejaron pasar el error, no a quién señalar.

| | |
| --- | --- |
| **Estado** | Acciones de detección cerradas y verificadas en un segundo simulacro (ver al final); la de prevención está pendiente |
| **Tipo** | Simulacro. Workflow `Simulacro de incidente`, corrida 42305538732, en docker compose con el volumen de QA-01. Reproduce el aviso de Render: «puede reiniciar una base gratuita en cualquier momento». |
| **Duración** | 29 min 41 s sin base (17:48:59 a 18:18:40, hora de Bogotá) |
| **Detectado por** | Alerta `PresupuestoQuemaRapida`, 1 min 45 s después del corte |
| **Runbook usado** | [`Runbook_base_de_datos.md`](../runbooks/Runbook_base_de_datos.md) |
| **Presupuesto de error consumido** | Cerca del 30 % del presupuesto de 14 días (29,7 de 100,8 minutos permitidos con el SLO del 99,5 %) |

## Resumen

Durante media hora de tarde, FitManage no pudo llegar a PostgreSQL y la consulta de estado de recepción respondió 500. La alerta rápida avisó a tiempo y el runbook encontró la causa en un minuto. El problema serio fue otro: a los 15 minutos de la caída, el SLI empezó a mostrar el servicio como sano y la alerta rápida se apagó a las 18:04, catorce minutos antes de que la base volviera. Si el responsable hubiera cerrado el incidente porque la alerta se apagó, lo habría cerrado con el gimnasio todavía sin servicio.

## Impacto

- 3.061 consultas de estado respondieron 500 y otras miles respondieron 401 desde las 17:59. Las 401 no eran errores del usuario: el token de la sesión venció y no se pudo renovar, porque la base estaba caída.
- En recepción, en un caso real, media hora de verificación manual con la hoja del paso 1.
- Sin pérdida de datos: PostgreSQL se apagó de forma ordenada y la app volvió a conectarse sola.

## Línea de tiempo (hora de Bogotá)

| Hora | Qué pasó |
| --- | --- |
| 17:43:59 | Empieza el tráfico de recepción: 5 usuarios con k6, unas 4,8 peticiones por segundo. |
| 17:48:59 | La base deja de responder. Las consultas pasan a 500. |
| 17:50:44 | `PresupuestoQuemaRapida` se dispara (1 min 45 s). |
| 17:51:59 | Paso 2 del runbook: `/salud` da **503 `SERVICIO_NO_DISPONIBLE`**; el contenedor `db` está *exited*; `pg_isready` responde «service "db" is not running»; el último error de la app es `OperationalError: failed to resolve host 'db'`. Caso B del paso 3: la base no está, la app sí. |
| 17:54:44 | `PresupuestoQuemaLenta` se dispara. |
| ~17:59 | Vence el token de acceso (dura 15 minutos). El cliente no puede renovarlo y las consultas pasan de 500 a **401**. |
| 18:04:14 | **`PresupuestoQuemaRapida` se apaga.** El SLI solo contaba la consulta de estado y trataba los 401 como respuestas correctas. La base sigue caída. |
| 18:18:40 | Paso 4 del runbook: `docker compose start db`; `pg_isready` acepta conexiones en el mismo segundo. |
| 18:18:40 a 18:19:00 | Paso 5: `/salud` responde 200 tres veces. La app se reconectó sola, sin reiniciarla. |
| 18:24:59 | Termina el tráfico. El cliente de prueba nunca volvió a iniciar sesión, así que siguió recibiendo 401 hasta el final. |

## Causa raíz

La caída de la base es un evento de la plataforma, aceptado en el ADR N.° 14: la base gratuita no tiene réplica. Lo que hay que corregir es por qué la medición se equivocó. Cinco porqués:

1. ¿Por qué se apagó la alerta con la base caída? Porque la proporción de 5xx bajó de 100 % a 0 % a las 17:59.
2. ¿Por qué bajó? Porque las consultas pasaron a responder 401, y el SLI cuenta un 401 como respuesta correcta.
3. ¿Por qué 401? Porque el token venció a los 15 minutos, y renovarlo o iniciar sesión otra vez necesita la base.
4. ¿Por qué el SLI no vio esas renovaciones fallidas? Porque el SLI se definió por **endpoint** (solo la consulta de estado) y no por el **recorrido del usuario**, que en recepción es iniciar o renovar la sesión y consultar.
5. ¿Por qué no se detectó antes? Porque ninguna prueba combinaba «la base cae» con «el token vence», y el tráfico de prueba no se comportaba como un cliente real, que intenta renovar la sesión.

## Qué funcionó

- La alerta rápida avisó en 1 min 45 s, bien dentro de los 5 minutos que aguanta recepción antes de pasar al papel.
- El diagnóstico del runbook distinguió «app viva, base caída» en un minuto y sin cambiar nada.
- La app se recuperó sola: `CONN_HEALTH_CHECKS` hizo su trabajo y no hubo que reiniciarla.
- El paso 5 del runbook exige `/salud` en 200 tres veces, no que la alerta se apague. Eso habría evitado cerrar el incidente en falso.

## Qué no funcionó

- El SLI mostró una recuperación que no existía durante 14 minutos.
- El cliente de prueba nunca volvió a iniciar sesión después de que volvió la base.

## Dónde tuvimos suerte

- Fue un simulacro. En un caso real, el correo «alerta resuelta» de las 18:04 habría invitado a dejar de mirar.
- La alerta lenta, que mira 6 horas, siguió disparada todo el tiempo y no se dejó engañar.

## Acciones

| Acción | Tipo | Responsable | Fecha | Estado |
| --- | --- | --- | --- | --- |
| El SLI de disponibilidad cubre el recorrido de recepción: `auth/token`, `auth/renovacion` y la consulta de estado. | Detectar | Juan Sebastián Cárdenas | 6/11/2026 | Hecha (`slo.yml`) |
| Prueba de `promtool` para «token vencido durante la caída»: las consultas dan 401 y el inicio de sesión da 500; la alerta debe seguir disparada. | Detectar | Juan Sebastián Cárdenas | 6/11/2026 | Hecha (`slo_test.yml`) |
| El tráfico del simulacro inicia sesión otra vez antes de que venza el token, como la app de recepción. | Detectar | Juan Sebastián Cárdenas | 6/11/2026 | Hecha (`trafico_observabilidad.js`) |
| El runbook dice explícitamente que una alerta apagada no cierra el incidente. | Mitigar | Juan Sebastián Cárdenas | 6/11/2026 | Hecha (paso 5) |
| Repetir el simulacro con las correcciones. | Verificar | Juan Sebastián Cárdenas | 6/11/2026 | Hecha (corrida 42312082387) |
| Pasar la base de Render al plan de US$6 antes de que venza la gratuita (2/12/2026), para tener copias de seguridad. | Prevenir | Juan Sebastián Cárdenas, con el visto bueno del gimnasio | 1/12/2026 | Pendiente |
| Agregar las rutas de sesión al SLO de las reglas creadas a mano en Grafana Cloud. | Detectar | Juan Sebastián Cárdenas | Próxima guía | Pendiente |

## Verificación de las acciones (segundo simulacro)

Corrida 42312082387 del mismo workflow, con las cuatro correcciones y el mismo escenario: 30 minutos sin base, de 18:35:10 a 19:04:53.

| | Primer simulacro | Segundo simulacro |
| --- | --- | --- |
| `PresupuestoQuemaRapida` se dispara | 1 min 45 s después del corte | 2 min después del corte |
| `PresupuestoQuemaRapida` se apaga | 18:04:14, **con la base caída** | 19:09:55, 5 min después de que volvió la base |
| Respuestas durante la caída | 500 y, desde los 15 minutos, 401 | 500 en la consulta y en el inicio de sesión, los 30 minutos |
| Después de la caída | 401 hasta el final: el cliente nunca volvió a entrar | 200: los usuarios de prueba iniciaron sesión otra vez (11 inicios correctos) |
| `/salud` en 200 tres veces | 18:18:40 a 18:19:00 | 19:04:53 a 19:05:13 |

La alerta ya no se engaña con el token vencido. Queda una observación para la próxima versión del tráfico de prueba: mientras la base estuvo caída, cada usuario reintentó iniciar sesión en cada iteración (6.661 intentos con 500 en 30 minutos). Una app real esperaría unos segundos entre reintentos. Eso no cambia la decisión de la alerta, que se dispara igual con mucho o poco tráfico, pero sí infla la cantidad de errores de la corrida.

Evidencia: `docs/guia-14-sw2/evidencia/simulacro1-42305538732.txt`, `simulacro2-42312082387.txt` y las capturas del tablero de cada corrida.
