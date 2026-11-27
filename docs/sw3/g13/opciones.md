# Regla de elegibilidad para anular · opciones y decisión (Software III, Guía 13)

**Regla (RF-10 v1.3):** puede anular el último pago vigente el administrador, o quien lo registró
si fue el mismo día en Bogotá.

| Opción | Dónde vive la regla | Dependencias que cruza | Fuerzas |
| --- | --- | --- | --- |
| A. Función directa dentro de `RecepcionistaCorrigeSuDia.exigir` (lo que había) | Un `if` en la política | Ninguna | Simple, pero solo sirve para rechazar. La pantalla necesitaba la misma respuesta **sin** excepción, así que `app.js` la reescribió comparando **nombres** y la hora del navegador. |
| B. Especificación `PUEDE_ANULAR = EsAdministrador() \| (LoRegistroQuienAnula() & RegistradoElMismoDia())` (elegida) | `dominio/especificaciones.py` | Ninguna: no conoce HTTP ni la base | Tiene un nombre del dominio, se prueba por partes (tabla de verdad) y la usan la política, para rechazar, y el historial, para decir `puedeAnular`. La pantalla ya no decide nada. |

**Por qué B y no A:** la regla tiene dos consumidores reales con preguntas distintas («¿lo rechazo?»
y «¿muestro el botón?»). Con un solo consumidor me habría quedado con A, como se pide en la
pregunta 7 de la guía.

**Lo que no es la especificación:** no es un filtro de consulta. Ninguna consulta SQL implementa
«registrado hoy por mí». Si un día el reporte necesitara listar «pagos que puedo anular», el
filtro tendría que probarse contra estos mismos casos antes de usarse.

## Evidencia

- `tests/nucleo/test_especificaciones.py`: tabla de verdad de la conjunción, disyunción del
  administrador, frontera 23:59:59 / 00:00:00 de Bogotá y dos personas con el mismo nombre. Corre
  sin interfaz ni base.
- `tests/integracion/api/test_api_administracion.py::test_el_historial_dice_que_pago_puede_anular_quien_consulta`.
- [`salida_antes.txt`](salida_antes.txt) y [`salida_despues.txt`](salida_despues.txt): con dos
  recepcionistas ficticias que se llaman igual, antes la pantalla le habilitaba el botón a la que
  no registró el pago (el servidor sí la rechazaba al confirmar); ahora lo deshabilita.
