# Evidencia de la Guía 16 (FPI-32)

## Pantalla de recepción (ADR N.° 16)

`e2e.js` recorre el flujo con Chromium (Playwright) contra gunicorn local, con la base creada por `preparar_gimnasio`: inicio de sesión fallido y correcto, consulta de un documento que no existe, registro del socio, pago Mensual por Nequi y la consulta final. Para probar PA-11, el formulario de pago se envía dos veces seguidas: la base queda con **un** pago.

| Captura | Qué muestra |
| --- | --- |
| `01-ingreso.png` | Inicio de sesión. |
| `02-no-registrado.png` | Documento sin socio, con el botón «Registrar socio». |
| `03-registro-socio.png` | Registro con la autorización y el aviso de que el texto legal está pendiente (DT-10). |
| `04-pago.png` | Formulario de pago: plan, medio y comprobante; el valor y las fechas los calcula el servidor. |
| `05-activo.png` | «Puede entrar»: 30 días, vence el 5/12/2026. |
| `06-celular.png` | La misma consulta en un Pixel 7. |
| `07-oscuro.png` | Tema oscuro del sistema. |

La primera corrida encontró un defecto real: el `pattern` del comprobante no era válido en Chrome (issue #38, BUG-01). Corregido; en la corrida final la consola solo muestra el 401 del inicio de sesión fallido a propósito y el 404 del documento no registrado.

## Licencias

`licencias-dependencias.md`: las 49 dependencias de ejecución con su licencia, generadas con `pip-licenses` desde `requirements.txt`. El check `sca-dependencias` repite el cálculo en cada PR y falla con una licencia fuera de la lista permitida.

## Ejercicio 5

[`../ejercicio-ia/README.md`](../ejercicio-ia/README.md): la IA auditora reconoció las 15 alucinaciones, pero convirtió en hechos cinco cosas que solo fueron propuestas.

## Producción en Grafana Cloud (7/11/2026)

`grafana-produccion-24h.png`: el tablero de producción en las últimas 24 horas, con el tráfico de la prueba de la pantalla de recepción. 0,1 peticiones por segundo, **p95 de la consulta de estado: 108 ms**, **0,0 % de errores 5xx** y 0 alertas activas. La latencia es mayor que los 13,5 ms de QA-01 porque incluye la red y el plan gratuito de Render, y sigue lejos de los 2 s del RNF-01 y de los 500 ms del SLO.

El tablero mostró algo que ninguna prueba había visto: la mayor parte del tráfico eran respuestas **405**. `grafana-explore-405.png` lo aisló en Explore: eran peticiones `HEAD` a la raíz, etiquetadas `sin_ruta`. La pantalla de recepción solo aceptaba `GET`, y los monitores de disponibilidad preguntan con `HEAD`. Se corrigió (`require_safe`) y la raíz ahora se etiqueta como `/`; las dos cosas tienen su prueba.

## Alertas de Dependabot (7/11/2026)

Se activaron las alertas y las actualizaciones de seguridad de Dependabot en el repositorio. El workflow `Resumen Dependabot` las lee con un token fine-grained de solo lectura (secreto `DEPENDABOT_LECTURA`) y deja el resultado en la corrida; se ejecuta cada lunes y a mano. Primera lectura: **0 alertas abiertas** (corrida [42430495784](https://github.com/GAMERO29/FitManage/actions/runs/42430495784)). Coincide con los checks `sca-dependencias` y `sca-imagen`, que tampoco encuentran vulnerabilidades críticas o altas sin mitigar.
