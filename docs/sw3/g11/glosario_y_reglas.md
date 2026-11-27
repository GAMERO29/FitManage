# Glosario e invariantes del contexto «Pagos y membresías» · Software III, Guía 11

Origen de cada término: ERS 1.0 (línea base v1.2), requisitos v1.3 (`docs/sw3/g10`) y código.

## Glosario

| Término | Definición para el equipo | Responsable en el código | Origen |
| --- | --- | --- | --- |
| Socio | Persona inscrita en el gimnasio. No es «usuario»: el usuario es del personal. | `dominio.modelos.Socio` | ERS §2, terminología |
| Pago vigente | Pago **no anulado**, aunque su periodo ya haya pasado. Un pago de enero sigue «vigente» en junio. | `Pago.esta_vigente()` | ERS §4, P01 |
| Membresía activa | Hoy ≤ el vencimiento más lejano de los pagos vigentes. No se guarda: se calcula (RN-05). | `CalculadoraMembresia.estado_de`, `HistorialPagos.estado` | RN-05 |
| Periodo | Días que cubre un pago, de `inicia` a `vence`, ambos incluidos (RN-03). | `dominio.modelos.Periodo` | RN-03, Guía 08 |
| Renovación anticipada | Pagar antes de vencer; el nuevo periodo inicia el día siguiente al vencimiento. | `HistorialPagos.periodo_del_siguiente` | RN-04 |
| Anulación | Marcar un pago como anulado con motivo, quién y cuándo. El pago no se borra. | `Pago.anular` + `HistorialPagos.exigir_que_sea_el_ultimo` | RN-07 v1.3 |
| Cambio de plan | Anular el último pago y registrar otro plan desde el mismo día de inicio, en una sola operación. | `CambioPlanService` | ADR N.° 18 |

## Caso ambiguo y aclaración

«Vigente» tenía dos significados. En la pantalla y al hablar con el gimnasio, «vigente» es «al día»;
en el código, «pago vigente» es «no anulado». La frase «solo se anula el último pago vigente»
se leía como «solo se anula el pago de la membresía actual». Pero si un socio pagó en octubre y
venció en noviembre, el pago de octubre sigue siendo **el último pago vigente** y se puede anular
aunque la membresía esté vencida. **Aclaración:** en documentos y código, «vigente» se usa solo
para pagos (no anulado). Para la membresía se dice «activa», «vencida» o «sin membresía».

Hay otro término con dos sentidos: **renovación**. Es RN-04 (pagar antes de vencer) y también el
token de renovación de la sesión (`/auth/renovacion`). Viven en contextos distintos (pagos y
acceso), así que se acepta. En los textos de pagos se escribe «renovación anticipada».

## Invariantes

| ID | Condición → efecto | Dónde se protege | ¿Coordinación en la misma operación? |
| --- | --- | --- | --- |
| I-1 | Si un pago no es el último vigente de su socio → no se anula | `HistorialPagos.exigir_que_sea_el_ultimo` | Sí: lectura de los pagos del socio y escritura del pago, con la fila del socio bloqueada |
| I-2 | Un pago nuevo → su periodo empieza después del vencimiento más lejano o hoy; nunca se solapa | `HistorialPagos.periodo_del_siguiente` | Sí: mismo bloqueo, para que dos cobros simultáneos no calculen el mismo inicio |
| I-3 | Un pago cuyas fechas no corresponden a su duración → no existe | `Pago.__post_init__` (Guía 08) | No: es interna del pago |
| I-4 | Un pago anulado → tiene motivo, responsable y fecha | `Pago.anular` y la restricción CHECK de la migración 0003 | No |
| I-5 | Una referencia de comprobante → a lo sumo en un pago vigente, **de cualquier socio** | Índice único parcial en PostgreSQL; el servicio solo avisa antes | Cruza agregados: no se bloquea a todos los socios, lo resuelve la base |
| I-6 | Una operación sobre pagos que se confirma → deja su evento de auditoría, y si falla, ninguno de los dos queda | `transaction.atomic()` en la vista | Sí: pago y evento en la misma transacción |

## Límite de consistencia

El agregado es **el historial de pagos de un socio**, con raíz `HistorialPagos` y candado la fila
del socio (`bloquear_socio_por_documento` y `bloquear_socio_del_pago`). Los cambios de estado de un
pago los hace `Pago.anular`, y solo después de que la raíz dice que es el último. El plan y el
usuario se referencian por identidad y no forman parte del agregado: desactivar un plan no
bloquea los pagos de nadie.
