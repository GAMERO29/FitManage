# Auditoría de IA · Guía 13 (versión de la regla)

**Prompt.** «Escribe en Python la regla de FitManage para saber si un usuario puede anular un
pago: el administrador siempre puede; la recepcionista solo si registró el pago ella misma y fue
hoy.» Salida en [`propuesta_ia.py`](propuesta_ia.py).

## Contraste con el catálogo de reglas

| Aspecto | IA | Catálogo (RF-10 v1.3) | ¿Coincide? |
| --- | --- | --- | --- |
| Operadores | `admin or (mismo_nombre and hoy)` | `admin | (lo_registró & mismo_día)` | Sí, con el paréntesis correcto. |
| Orden de evaluación | Cortocircuito: si es administrador no mira lo demás | Igual | Sí. |
| «Ella misma» | Compara `nombre` | Identidad del usuario (`id`) | **No.** Dos personas con el mismo nombre pasan por la misma. |
| «Hoy» | `registrado_en.date()` en UTC contra `date.today()` del servidor | Día de Bogotá, con el reloj inyectado | **No.** Render corre en UTC: después de las 7 p. m. de Bogotá cambia el día. |

**Verificación con los casos** ([`verificacion_ia.txt`](verificacion_ia.txt), corrida con
`TZ=UTC` a las 6 p. m. de Bogotá): la IA falla 3 de 4. Rechaza a Laura con su pago de las 8 p. m.,
acepta el de ayer a la misma hora y acepta a otra persona con el mismo nombre. `PUEDE_ANULAR`
pasa los 4. El resultado de la IA cambia según la hora en que se corra, y ese es justamente el
defecto.

**Corrección.** Se mantiene la especificación con identidad y día de Bogotá. La comparación por
nombre que tenía nuestra propia pantalla era el mismo error, y se eliminó (ver [`opciones.md`](opciones.md)).

**Limitación.** La misma sesión generó y auditó la regla.
