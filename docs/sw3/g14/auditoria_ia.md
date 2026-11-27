# Auditoría de IA · Guía 14 (estrategia de persistencia)

**Prompt.** «En una API Django con PostgreSQL, ¿cómo persistirías la anulación de un pago y su
evento de auditoría? Muestra dónde abres y confirmas la transacción.» Sin datos ni credenciales.

**Fragmento relevante.**

```python
def anular_pago(request, pago_id):
    pago = Pago.objects.get(id=pago_id)
    pago.estado = "ANULADO"
    pago.motivo = request.data["motivo"]
    pago.save()                                   # autocommit: queda confirmado aquí
    try:
        Auditoria.objects.create(tipo="PAGO_ANULADO", entidad=pago.id)
    except Exception:
        logger.warning("no se pudo auditar")      # «la auditoría no debe tumbar la operación»
    return Response(PagoSerializer(pago).data)
```

## Revisión

| Pregunta | Respuesta para la propuesta |
| --- | --- |
| ¿Dónde abre y confirma? | No abre nada: cada `save()` se confirma solo (autocommit). |
| ¿Divide escrituras que deben ser atómicas? | **Sí.** El pago queda anulado aunque el evento falle, y el `except` lo esconde. Es justo lo que prohíbe la invariante I-6 de la Guía 11 y el ADR N.° 19. |
| ¿Qué pasa al repetir? | No revisa si ya estaba anulado: la segunda llamada vuelve a escribir el motivo y otro evento. Tampoco bloquea al socio, así que dos anulaciones simultáneas pasan las dos (el D-01 de la Software II). |
| ¿Reglas? | Asigna `estado` directamente: se salta `Pago.anular` (motivo de 5 caracteres, una sola vez) y la regla de arquitectura de la Guía 08 lo marcaría. |

## Caso con el que se verificó

`tests/integracion/api/test_api_auditoria_pagos.py::test_si_la_auditoria_falla_la_anulacion_se_revierte`
inyecta un fallo justo donde la propuesta pone el `try`. Con el diseño de FitManage (vista con
`transaction.atomic()`, bloqueo del socio y servicio que guarda y audita) el pago sigue VIGENTE,
sin motivo ni responsable, y no queda evento. Con la propuesta, el pago habría quedado ANULADO
sin rastro. La repetición se verificó en el laboratorio: segunda anulación 409 y un solo evento
(`persistencia_salida.txt`).

**Corrección.** Se mantiene la transacción en la vista que envuelve servicio, pago y evento, y la
auditoría nunca se traga un error. **Limitación:** la misma sesión generó y auditó la propuesta.
