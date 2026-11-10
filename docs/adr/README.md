# Registros de decisión de arquitectura (ADR)

Un ADR aceptado no se edita. Si la decisión cambia, se escribe uno nuevo y el anterior pasa a «Reemplazado por ADR-0X»; solo se toca su campo Estado.

| N.° | Decisión | Estado | Fecha |
| --- | --- | --- | --- |
| [01](ADR-001-linea-base-y-puerta-de-calidad.md) | Congelar la línea base LB-1 y exigir una puerta de calidad automática | Aceptado | 30/10/2026 |
| [02](ADR-002-drivers-arquitectonicos.md) | Drivers arquitectónicos priorizados | Aceptado | 30/10/2026 |
| [03](ADR-003-unidad-de-despliegue.md) | Una sola aplicación Django con plantillas en el servidor y una API mínima para la caché sin conexión | Aceptado | 30/10/2026 |
| [04](ADR-004-estilo-arquitectonico.md) | Monolito modular con núcleo hexagonal en los módulos que tocan dinero | Aceptado | 30/10/2026 |
| [05](ADR-005-distribucion.md) | Ningún contexto se distribuye: todo sigue en el monolito modular, con límites lógicos | Aceptado | 30/10/2026 |
| [06](ADR-006-seguridad-api-jwt.md) | La API `/api/v1` se protege con JWT de acceso corto y renovación en cookie `HttpOnly`; la web sigue con sesión | Aceptado | 31/10/2026 |
| [07](ADR-007-estrategia-de-pruebas.md) | Pirámide de pruebas con base efímera real y dobles solo en las fronteras externas; contrato verificado en cada respuesta y con Pact | Aceptado | 31/10/2026 |
| [08](ADR-008-rendimiento-consulta-recepcion.md) | La consulta de recepción se vigila con k6 contra un entorno de carga local; conexiones persistentes a PostgreSQL y sin caché | Aceptado | 02/11/2026 |
| [09](ADR-009-pipeline-ci-y-quality-gate.md) | El pipeline `CI` es la única puerta a `main`: cinco checks requeridos, Quality Gate en dos capas e imagen inmutable por commit | Aceptado | 02/11/2026 |
| [10](ADR-010-contenedores.md) | Imagen multietapa sobre `python:3.12-slim-trixie` sin root; Compose con la base en un volumen dentro de una red interna | Aceptado | 02/11/2026 |
| [11](ADR-011-despliegue-continuo.md) | Despliegue continuo a Render desde la imagen de CI, con healthcheck de versión y rollback a `estable` | Aceptado | 02/11/2026 |
| [12](ADR-012-devsecops-sast-sca.md) | Semgrep y Trivy bloquean los hallazgos críticos y altos en el pipeline; cada excepción tiene razón y vencimiento | Aceptado | 02/11/2026 |
| [13](ADR-013-observabilidad.md) | OpenTelemetry con trazas al 10 %, métricas para Prometheus y logs JSON sin datos personales; logs 7 días, métricas 15 días | Aceptado | 03/11/2026 |
| [14](ADR-014-slo-presupuesto-de-error.md) | SLO de la consulta de estado: 99,5 % de disponibilidad y 99 % bajo 500 ms en 14 días, alertas por consumo del presupuesto y congelamiento | Aceptado | 06/11/2026 |
| [15](ADR-015-mantenimiento-deuda-residual.md) | Pagar ahora la lógica en los controladores (DT-16), convivir con la deuda del prototipo y de `Pago`, roadmap con disparadores y Django 5.2 LTS hasta 6.2 LTS | Aceptado | 06/11/2026 |
| [16](ADR-016-pantalla-recepcion.md) | La pantalla de recepción es una página estática del mismo origen que consume la API; el primer arranque crea los planes y la primera cuenta | Reemplazado en la interfaz por el 17 | 06/11/2026 |
| [17](ADR-017-aplicativo-conectado.md) | El aplicativo del personal es el prototipo de la Guía 4 conectado a la API, sin datos ni reglas propias | Aceptado | 07/11/2026 |
| [18](ADR-018-recepcionista-corrige-pagos.md) | La recepcionista anula sus pagos del día y cambia el plan de un socio | Aceptado | 09/11/2026 |
| [19](ADR-019-auditoria-solo-insercion.md) | Rastro de auditoría de solo inserción, en la misma transacción y en la misma base | Aceptado | 09/11/2026 |

Los ADR 01 y 02 se escribieron con la plantilla de 5 campos de la Guía 1. Desde el ADR 03 se usa la plantilla completa de 6 campos (`plantilla.md`), que agrega las alternativas consideradas. Los dos primeros no se reescriben para cumplirla, precisamente porque un ADR aceptado es inmutable.
