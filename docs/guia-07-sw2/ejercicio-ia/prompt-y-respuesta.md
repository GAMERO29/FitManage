# Ejercicio 5 · Suite de integración generada por IA para `POST /api/v1/pagos`

**Herramienta:** Claude (Anthropic), sesión nueva. **Fecha:** 31/10/2026. Le pegué `docs/api/openapi.yaml` (solo la operación `registrarPago` y sus esquemas) y `aplicacion/pagos.py`.

## Prompt

> Tengo una API en Django (proyecto FitManage) con el endpoint POST /api/v1/pagos que sigue este contrato OpenAPI y usa este servicio. Genera una suite de pruebas de integración con pytest para ese endpoint: caso exitoso, cálculo del vencimiento, referencia duplicada y error del servicio.

## Respuesta de la IA (sin modificar)

El archivo completo está en [`test_pagos_ia.py.txt`](test_pagos_ia.py.txt) (con extensión `.txt` para que pytest no lo recoja; **nunca** se corrió). El texto que lo acompañaba:

> Esta suite prueba el endpoint de extremo a extremo haciendo peticiones HTTP reales al servidor de desarrollo con `requests`, así verificas la integración completa. La fixture `datos` crea el plan y el socio en la base y los limpia al final para dejarla como estaba. Para que las pruebas sean deterministas, se mockean `CalculadoraMembresia` y el repositorio, y así controlas exactamente el vencimiento y el caso de referencia duplicada. Recuerda tener el servidor corriendo con `python manage.py runserver` antes de ejecutar `pytest`.

## Auditoría y corrección

Ver el Ejercicio 5 de la guía resuelta y la tabla de la FPI-23. La suite corregida es `tests/integracion/api/test_api_pagos.py`.
