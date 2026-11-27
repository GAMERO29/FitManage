# Requisitos congelados para el diseño · línea base de requisitos v1.3

Software III, Guía 10. Toma la línea base v1.2 de la ERS 1.0 (7/10/2026) y la ajusta con el
ADR N.° 18 (9/11/2026), que la ERS nunca incorporó (hallazgo H-10-01 de [`revision.md`](revision.md)).
Esta versión cubre solo los tres requisitos que se diseñan y verifican en esta guía; el resto de la
ERS sigue en v1.2.

| Campo | Valor |
| --- | --- |
| Versión | v1.3 (congelada el 27/11/2026) |
| Base | ERS 1.0 · línea base v1.2 · ADR N.° 18 |
| Aprueba | Juan Sebastián Cárdenas Acevedo (líder técnico); el dueño del gimnasio valida en el piloto |
| Pendiente | CR-02 (motivo con al menos 5 caracteres en el dominio), aceptada; pasa a v1.4 cuando se cierre |

## RF-03 · Registrar pago (sin cambios desde v1.2)

El sistema debe permitir a la recepcionista registrar el pago de una membresía indicando plan,
medio de pago (efectivo, Nequi, Daviplata o transferencia) y, si el medio no es efectivo, la
referencia del comprobante. El sistema calcula la fecha de inicio (hoy, o el día siguiente al
vencimiento vigente si el socio renueva antes de vencer) y la fecha de vencimiento como
inicio + duración − 1 día, en America/Bogota. El valor es el precio completo del plan.
Reglas: RN-03, RN-04, RN-06, RN-08.

## RF-10 · Anular pago (cambia en v1.3)

**v1.2:** «El sistema debe permitir al administrador anular el último pago vigente de un socio…»

**v1.3:** El sistema debe permitir anular el último pago vigente de un socio, indicando un motivo
obligatorio. Lo puede hacer el administrador con cualquier pago, y la recepcionista solo con un
pago que ella misma registró ese mismo día (hasta las 23:59:59 de America/Bogota). El pago no se
borra: queda marcado como anulado con usuario, fecha y motivo, se excluye de los ingresos, la
membresía se recalcula y la anulación queda en la auditoría. Regla: RN-07 v1.3.

## RNF-05 · Control de acceso (cambia en v1.3; requisito de calidad)

**v1.2:** «La recepcionista no accede a reportes de ingresos ni a la anulación; todo acceso no
autorizado responde con error 403.»

**v1.3:** La recepcionista no accede a reportes de ingresos, a la auditoría, a la administración
de cuentas ni a la supresión de socios, y solo anula según RF-10 v1.3. Todo acceso no autorizado
responde 403 en problem+json, sin cambiar datos ni registrar eventos. Se verifica en cada
operación del contrato que exige rol.
