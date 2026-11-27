# Software III · Guía 04 · Registro de cambio CR-01 y su versión en incrementos

## La solicitud

**CR-01.** «Que la recepcionista no pueda pasar a un socio a un plan más barato sin que lo apruebe el administrador.»

Origen: el propio ADR N.° 18 lo deja como disparador de revisión. Allí se acepta un riesgo: el cambio de plan anula el pago anterior aunque sea de otro día, así que una recepcionista podría cambiar a un socio de Mensual ($ 75.000) a Quincenal ($ 45.000) y quedarse con los $ 30.000 que «devuelve». Desde el ADR N.° 19 ese movimiento queda en la auditoría (`PLAN_CAMBIADO`, con la diferencia), pero queda después de que pasó.

## Recorrido clásico: control por línea base

| Campo | Contenido |
| --- | --- |
| Línea base afectada | LB-SW3-01: commit `1790310` (v1.1.0 más las correcciones H-01 a H-03), contrato `docs/api/openapi.yaml` 1.7.0, ADR N.° 18 y 19. |
| Requisitos afectados | RF-10 (corregir pagos), RN-07 (anulación con motivo) y la restricción del DAD 4.2 que ya modificó el ADR N.° 18. |
| Diseño impactado | `CambioPlanService.cambiar` (`aplicacion/pagos.py`), la pantalla del historial (`infraestructura/web/app.js`), el contrato de `POST /pagos/{pagoId}/cambio-de-plan` (un 403 nuevo), la tabla de auditoría si se registra la solicitud. |
| Pruebas afectadas | `tests/integracion/api/test_api_cambio_plan.py`: cambia el resultado esperado de `test_la_recepcionista_cambia_el_plan_aunque_el_pago_sea_de_otro_dia` cuando el plan nuevo es más barato. Hacen falta pruebas nuevas para «igual o más caro», «más barato» y «el administrador sí puede». |
| Impacto en datos | Ninguna migración si solo se rechaza. Si se guarda la solicitud pendiente, una tabla nueva y su migración. |
| Responsable | Juan Sebastián Cárdenas Acevedo (desarrollo). Aprobador propuesto: el dueño del producto, que es quien pidió el ADR N.° 18. |
| Verificación | Las pruebas nuevas en verde, la suite en PostgreSQL y el recorrido de la Guía 01 sin cambios en los pasos que no tocan el cambio de plan. |
| Decisión del control | Se aprueba la versión que solo rechaza (sin tabla nueva) y se aplaza la aprobación en línea. Después de la aprobación se actualizan la línea base (LB-SW3-02), el ADR N.° 18 (nuevo ADR que lo reemplaza en esa parte) y el contrato 1.8.0. |

## Recorrido evolutivo: dos incrementos

| Incremento | Qué entrega | Criterio de aceptación | Decisión reversible | Riesgo que reduce |
| --- | --- | --- | --- | --- |
| I-1 | El servidor rechaza con 403 el cambio de plan de la recepcionista cuando el plan nuevo vale menos. El mensaje dice «Pídale al administrador este cambio». El administrador no tiene el límite. | Tres pruebas: recepcionista a un plan más caro (201), recepcionista a uno más barato (403 y el pago anterior sigue vigente), administrador a uno más barato (201). | La regla es una política inyectada, igual que la `PoliticaAnulacion` de la Guía 03; volver atrás es cambiar la política en el contenedor. | El fraude descrito en el ADR N.° 18. |
| I-2 | Solicitud de aprobación: la recepcionista deja el cambio pendiente y el administrador lo aprueba o rechaza desde Auditoría. | El cambio solo se aplica con la aprobación; la auditoría muestra quién pidió y quién aprobó. | Se decide solo si I-1 muestra que el socio se queda esperando demasiado. | Que la recepción dependa de que el administrador esté en el gimnasio. |

**Demostración que decide si I-2 se mantiene:** después de dos semanas con I-1, contar en la auditoría cuántos cambios a un plan más barato tuvo que hacer el administrador y cuánto tardó cada uno desde que el socio lo pidió. Si son pocos y se resolvieron el mismo día, I-2 no se construye.

## Comparación de los dos recorridos para CR-01

| Criterio | Clásico (línea base) | Evolutivo (incrementos) |
| --- | --- | --- |
| Costo de un error | Bajo: el análisis de impacto se hace antes de tocar código. | Bajo también, porque I-1 se revierte cambiando una política. |
| Estabilidad del requisito | La regla de fondo es estable (proteger el dinero); el flujo de aprobación no lo es. | Encaja con la parte inestable: I-2 se decide con datos. |
| Tiempo de retroalimentación | La primera evidencia llega cuando se aprueba y se construye todo. | I-1 se puede probar en un día. |
| Documentación mínima | Registro de cambio, línea base nueva, ADR, contrato. | Criterio de aceptación de cada incremento, ADR que reemplaza en parte al 18 y el contrato 1.8.0 de I-1. |

**Decisión:** combinar. CR-01 pasa por el control de cambio porque modifica una decisión aceptada (ADR N.° 18) que afecta el dinero; dentro de lo aprobado se construye I-1 y se deja I-2 para decidirlo con la evidencia de la auditoría.

## Revisión simulada del cambio

No hubo otro equipo. La revisión la hice yo con la lista de verificación de este registro, y está marcada como simulada.

| Observación | Severidad | Decisión |
| --- | --- | --- |
| «Más barato» se compara contra el valor pagado, no contra el precio actual del plan: un plan pudo subir de precio después del pago. | Media | Se compara `valorNuevo` con `valorAnterior` del pago anulado, los mismos campos que ya guarda el evento `PLAN_CAMBIADO`. |
| El 403 de I-1 no debe confundirse con el 403 de «otro rol»: la pantalla tiene que decir qué hacer. | Baja | El mensaje nombra al administrador. Se agrega a la guía rápida de la recepción. |

Estado de CR-01: aprobado para I-1, pendiente de construir. I-2 queda sin decidir hasta tener la evidencia descrita.
