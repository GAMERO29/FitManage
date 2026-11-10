# Hallazgos de la Guía II-06

Origen: revisión del autor sobre la versión v1.1.0, recorriendo las tareas del protocolo y el incidente de II-05 desde el punto de vista de la recepcionista. **No vienen de participantes.** Son hallazgos de inspección, con el sesgo de quien diseñó la interfaz.

| Id | Observación | Consecuencia | Hipótesis | Prioridad | Decisión y cambio | Nueva comprobación |
| --- | --- | --- | --- | --- | --- | --- |
| H-01 | Con la base caída (laboratorio de II-05), la consulta muestra «El servidor respondió 500. Intente de nuevo.» | La recepcionista repite la consulta sin fin mientras la fila crece; el mensaje no menciona el plan B en papel del ADR N.° 14. | El texto genérico se escribió para errores raros y no para una caída. | Alta: mensaje engañoso en la tarea principal. | `mensajeDe`: un 5xx sin código del contrato, o `SERVICIO_NO_DISPONIBLE`, dice qué hacer (papel, avisar, reintentar en un minuto). `CORREO_NO_DISPONIBLE` conserva su mensaje. | `caida.js` con la base detenida de verdad (`caida_salida.txt`, capturas antes y después) y `mensajes.js`, 4 de 4 casos simulados. |
| H-03 | En la misma caída, el menú sigue diciendo «En línea con el servidor». | Contradice el mensaje de error; la persona puede pensar que el problema es suyo. | El indicador solo mira `navigator.onLine` (la red del equipo), no al servidor. | Alta: contradice el aviso de H-01. | El indicador refleja la última respuesta del servidor: «El servidor no responde: use la hoja de papel». Vuelve a «En línea» con la primera respuesta buena. | `caida.js` (vuelve a «En línea» al arrancar la base) y `mensajes.js`. |
| H-02 | En el historial, «$ 75.000» se parte en dos líneas («$» arriba, el número abajo). | Lectura más lenta de montos al corregir un cobro. | `pesos()` usa un espacio normal y la celda no impide el salto. | Media: no bloquea, pero confunde con dinero. | `white-space:nowrap` en `td.der` y `th.der`. | `montos.js` en 8 anchos, de 390 a 1366 px: antes se partían 2 o 3 de 3 montos en todos los anchos; después, 0. |
| H-04 | No hay ayuda dentro de la aplicación. | T5 solo se resuelve con la guía rápida impresa. | Nunca se planeó ayuda en línea. | Baja mientras haya guía impresa. | Se conserva: guía rápida impresa en la recepción. Va al backlog si la validación muestra que no la encuentran. | Pendiente de T5 con participantes. |
| H-05 | En T3 (era Quincenal y se cobró Mensual por Nequi), FitManage registra el plan nuevo, pero no la devolución de la diferencia. | Puede descuadrar la caja frente a los reportes. | Fuera del alcance de las reglas actuales (RN-07). | Por investigar: es una pregunta del oficio, no un defecto. | Se pregunta en la validación cómo se maneja hoy. | Pendiente. |

## Límite de la nueva comprobación

Las pruebas de regresión confirman que el mensaje y el indicador cambiaron, y que el escenario de auditoría A1 a A8 sigue pasando (8 de 8). No confirman que una recepcionista entienda mejor el mensaje nuevo: eso necesita observar a alguien del perfil, y que no sea la misma persona antes y después, por el efecto de aprendizaje.

## Un error de medición que corregí

La primera medición de H-02 dio 0 montos partidos también **sin** la corrección. El servidor seguía sirviendo el CSS que había cargado al arrancar. Repetí la medición reiniciando el servidor entre «antes» y «después» y ahí apareció el problema. Las salidas de `montos_salida.txt` son de esa segunda medición.
