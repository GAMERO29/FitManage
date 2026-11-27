# Auditoría de IA · Guía 08 (modelo de clases)

**Prompt.** «Propón el modelo de clases del dominio de FitManage (socios, planes, pagos y
membresías de un gimnasio) en Python, con sus atributos y métodos.» Sin datos de personas.

**Salida relevante.** [`propuesta_ia.py`](propuesta_ia.py): una clase `Membresia` con el documento
del socio como identidad, `fecha_vencimiento = inicio + duración`, un campo `estado` guardado y un
`set_estado()` público.

## Contraste con los requisitos

| Punto | Requisito | Resultado de la verificación ([`verificacion_ia.txt`](verificacion_ia.txt)) |
|---|---|---|
| Vencimiento | RN-03: vence = inicio + duración − 1 | **Error de un día.** La propuesta vence el 6 de noviembre y deja entrar ese día; FitManage vence el 5. |
| Estado guardado con setter | RN-05: el estado se deriva de los pagos vigentes; RN-07: la anulación es una operación con motivo | **Mutación directa sin regla.** `set_estado` acepta «ACTIVA-PREMIUM» y la membresía no sabe si su pago se anuló. |
| Identidad | El socio es una entidad con `id`; el documento puede corregirse | **Identidad frágil.** Con el documento como identidad, corregir un dígito crea «otro» socio. FitManage usa `id: UUID` y una restricción única aparte (RN-01). |

## Correcciones y evidencia

1. La regla de RN-03 queda en el objeto de valor `Periodo.de_plan` y la frontera exacta se prueba en
   `test_frontera_el_dia_del_vencimiento_todavia_entra` (el 5 de noviembre ACTIVO, el 6 VENCIDO).
2. Revisando la propuesta encontré que nuestro `Pago` tampoco validaba toda su invariante: solo
   exigía vencimiento ≥ inicio. Un pago de 30 días podía cubrir 90 ([`invariante_antes_despues.txt`](invariante_antes_despues.txt)).
   Ahora `Pago.__post_init__` exige que el periodo tenga exactamente `duracion_dias` días.
3. Contra la mutación directa: el estado del pago solo cambia con `Pago.anular()` y la regla
   `test_fuera_del_dominio_nadie_cambia_el_estado_asignando_atributos` falla si una capa externa
   asigna `estado`, `activo`, fechas o datos de anulación.

**Limitación.** La misma sesión generó y auditó la propuesta; cada observación se apoya en una
prueba que se puede volver a correr. La invariante nueva se revisó contra la base del laboratorio
(1 pago, 0 incoherentes, [`datos_existentes.txt`](datos_existentes.txt)); en producción todos los
pagos se crearon con `CalculadoraMembresia`, pero conviene correr la misma consulta antes de
desplegar.
