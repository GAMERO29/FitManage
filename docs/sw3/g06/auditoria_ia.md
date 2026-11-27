# Auditoría de IA · Guía 06 (borrador del contrato)

**Prompt.** «Escribe el contrato OpenAPI de una operación para que el administrador elimine a un
socio de FitManage.» Sin datos de socios.

**Fragmento relevante de la salida.**

```yaml
delete:
  summary: Eliminar socio
  responses:
    '200':
      description: Socio eliminado
      content:
        application/json:
          schema: { $ref: '#/components/schemas/SocioModelo' }
    '409':
      description: No se pudo eliminar el socio (tiene pagos u otro error)
```

## Revisión

| Punto | Criterio | Resultado |
|---|---|---|
| `200` con `SocioModelo` | ¿El contrato filtra entidades internas o datos personales? | **Filtra las dos cosas.** Expone el nombre del modelo del ORM y devuelve el documento y el celular de alguien que pidió que se borraran sus datos. |
| `409` «tiene pagos u otro error» | ¿Un error técnico queda disfrazado de error de negocio? | **Sí.** Con la base caída la recepción leería «el socio tiene pagos» y no reintentaría. Es el mismo problema de la ferretería con «saldo insuficiente». |
| Sin 403 ni 404 | ¿Están los permisos asumidos y el caso de socio inexistente? | Faltan. |

## Corrección y pruebas asociadas

- `204` sin cuerpo: `test_suprime_los_datos_de_una_socia_sin_pagos` comprueba ahora `r.content == b""`.
- `409 SOCIO_CON_PAGOS` solo para la regla: `test_un_socio_con_pagos_no_se_suprime`.
- `503 SERVICIO_NO_DISPONIBLE` en problem+json con `Retry-After`: `test_si_la_base_no_responde_es_503_y_no_cambia_nada`,
  y `test_toda_operacion_que_toca_la_base_declara_503` lo exige en todo el contrato.
- `403` y `404` declarados y probados (`test_la_recepcionista_no_suprime`, `test_repetir_la_supresion_responde_404`).

**Limitación.** La misma sesión generó y auditó el borrador.
