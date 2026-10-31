# Registros de decisión de arquitectura (ADR)

Un ADR aceptado no se edita. Si la decisión cambia, se escribe uno nuevo y el anterior pasa a «Reemplazado por ADR-0X»; solo se toca su campo Estado.

| N.° | Decisión | Estado | Fecha |
| --- | --- | --- | --- |
| [01](ADR-001-linea-base-y-puerta-de-calidad.md) | Congelar la línea base LB-1 y exigir una puerta de calidad automática | Aceptado | 30/10/2026 |
| [02](ADR-002-drivers-arquitectonicos.md) | Drivers arquitectónicos priorizados | Aceptado | 30/10/2026 |
| [03](ADR-003-unidad-de-despliegue.md) | Una sola aplicación Django con plantillas en el servidor y una API mínima para la caché sin conexión | Aceptado | 30/10/2026 |
| [04](ADR-004-estilo-arquitectonico.md) | Monolito modular con núcleo hexagonal en los módulos que tocan dinero | Aceptado | 30/10/2026 |
| [05](ADR-005-distribucion.md) | Ningún contexto se distribuye: todo sigue en el monolito modular, con límites lógicos | Aceptado | 30/10/2026 |

Los ADR 01 y 02 se escribieron con la plantilla de 5 campos de la Guía 1. Desde el ADR 03 se usa la plantilla completa de 6 campos (`plantilla.md`), que agrega las alternativas consideradas. Los dos primeros no se reescriben para cumplirla, precisamente porque un ADR aceptado es inmutable.
