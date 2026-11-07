# Evidencia de la Guía 14 (FPI-30)

## Reglas del SLO

`observabilidad/prometheus/slo.yml` tiene 6 reglas de registro (los SLI) y 4 alertas. El job `reglas-slo` del workflow `Observabilidad` corre `promtool check rules` y `promtool test rules` con los 8 casos de `observabilidad/prometheus/pruebas/slo_test.yml`: caída de la base, recuperación, errores bajos y constantes, errores dentro del presupuesto, consultas lentas, app sin responder, valor exacto del SLI y token vencido durante la caída.

## Simulacros de incidente (workflow `Simulacro de incidente`)

Mismo escenario en las dos corridas: tráfico de recepción con k6 sobre el volumen de QA-01 y la base apagada 30 minutos, atendida con `docs/runbooks/Runbook_base_de_datos.md`.

| | Corrida 42305538732 (primera) | Corrida 42312082387 (con las correcciones del postmortem) |
| --- | --- | --- |
| Base sin responder | 17:48:59 a 18:18:40 (hora de Bogotá) | 18:35:10 a 19:04:53 |
| `PresupuestoQuemaRapida` | 17:50:44 a 18:04:14: **se apagó con la base caída** | 18:37:10 a 19:09:55 |
| `PresupuestoQuemaLenta` | 17:54:44 hasta el final | 18:41:10 hasta el final |
| Paso 2 del runbook | `/salud` 503, `db` *exited*, `OperationalError` | igual |
| Recuperación | `/salud` 200 ×3 al encender la base, sin reiniciar la app | igual |
| Presupuesto consumido | cerca del 30 % de los 14 días | cerca del 30 % |

- [`simulacro1-42305538732.txt`](simulacro1-42305538732.txt) y [`simulacro2-42312082387.txt`](simulacro2-42312082387.txt): línea de tiempo, salida del diagnóstico y resumen de Prometheus.
- `simulacro1-tablero-*.png` y `simulacro2-tablero-*.png`: el tablero durante el incidente y al final. En la primera se ve el cambio de 500 a 401 a las 18:00 con la base caída.

Postmortem: [`docs/postmortems/2026-11-06-base-de-datos-30-minutos.md`](../../postmortems/2026-11-06-base-de-datos-30-minutos.md).
