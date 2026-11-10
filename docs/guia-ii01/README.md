# Guía II-01 · Análisis y modelado del flujo «Anular el último pago»

Versión analizada: `992ddc7` (lo que está en producción desde el 9/11/2026). Versión corregida: la rama de esta guía.

- `diagramas/`: fuentes Mermaid editables (`.mmd`) y sus imágenes: DFD de contexto y nivel 1, modelo lógico, secuencia y ciclo de anulación.
- `evidencia/recorrido.js`: recorrido técnico R1 a R13 con Playwright sobre el aplicativo real (gunicorn + PostgreSQL 16, base aislada, datos ficticios).
- `evidencia/recorrido_992ddc7.txt` y `recorrido_a358229.txt`: salida del recorrido antes y después de la corrección. En `992ddc7` falla R8 (dos anulaciones simultáneas responden 200 y 200).
- `evidencia/concurrencia_antes_992ddc7.txt` y `concurrencia_despues.txt`: las pruebas de `tests/integracion/api/test_api_concurrencia_socio.py` antes y después del bloqueo por socio.

La ficha de entrega completa (E1 a E8) está en el docx de la guía.
