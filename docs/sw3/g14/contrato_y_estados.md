# Anular un pago de extremo a extremo · contrato, estados y persistencia (Software III, Guía 14)

## Contrato del servicio (`PATCH /api/v1/pagos/{pagoId}`, `anularPago`, contrato 1.9.0)

| Entrada o estado | Capa y comportamiento | Evidencia |
| --- | --- | --- |
| `{"estado": "ANULADO", "motivo": "Se registró el plan equivocado"}` | Presentación valida la forma contra el contrato. Aplicación: `AnulacionPagoService.anular` revisa el rol, `HistorialPagos.exigir_que_sea_el_ultimo` y `PUEDE_ANULAR`. Dominio: `Pago.anular` con `MOTIVO_MINIMO`. Datos: guarda el pago y el evento en la misma transacción. → **200** con el pago anulado | `test_anular_deja_el_motivo_y_quien_registro_el_pago` |
| Motivo con menos de 5 caracteres | La pantalla avisa sin llamar; la API responde **400** por el contrato; el dominio lo rechaza igual (CR-02) si llega por otra vía | `estado_1_motivo_corto.png`, `test_un_motivo_de_menos_de_5_caracteres_no_anula` |
| Repetir la anulación | **409** con el detalle «El pago ya está anulado.»; no cambia nada ni deja otro evento | `persistencia_salida.txt` (2) |
| Base que no responde | **503** `SERVICIO_NO_DISPONIBLE` con `Retry-After: 60` (Guía 06). La pantalla dice qué hacer mientras tanto y conserva lo escrito; el mismo clic funciona al volver la base | `estado_2_base_caida.png`, `estado_3_anulado.png` |
| Recepcionista con un pago ajeno o de otro día | **403**; el botón ya llega deshabilitado por `puedeAnular` (Guía 13) | `test_un_rechazo_no_deja_evento[recepcionista-pago-ajeno]` |

**DTO de salida:** el esquema `Pago` del contrato, con `anulacion: {motivo, anuladoPor, anuladoEl}`.
No incluye el documento ni el teléfono del socio.

**Estados de la interfaz:** confirmando (formulario con motivo), error de validación (motivo
corto), error recuperable (base caída, con instrucción de contingencia), anulado (aviso y
historial recalculado) y conflicto (409: se recarga el historial con el estado actual).

## Decisión de mapeo

**Data Mapper.** `Pago` es un objeto del dominio sin Django. `infraestructura/persistencia/mapeo.py`
lo rehidrata desde `PagoModelo` y `PagoRepositorioORM` lo guarda. No se eligió Active Record
(que `Pago` fuera el modelo de Django) porque las invariantes de las Guías 08 y 11 se prueban sin
base en milisegundos y la regla de arquitectura impide que `dominio/` importe Django. El esquema
se versiona con migraciones de Django: la 0003 creó la auditoría y la coherencia de la anulación,
y la 0004 bloquea TRUNCATE.

**Frontera de la transacción:** la vista abre `transaction.atomic()`, bloquea la fila del socio y
llama al servicio. El pago anulado y el evento `PAGO_ANULADO` se confirman juntos.

## Pruebas de persistencia

| Prueba | Estado inicial y final | Resultado |
| --- | --- | --- |
| Atomicidad: fallo inyectado entre el pago anulado y el evento | VIGENTE, sin evento → VIGENTE, sin motivo ni responsable, sin evento | `test_si_la_auditoria_falla_la_anulacion_se_revierte`: pasa |
| Repetición del registro con la misma `Idempotency-Key` | 0 pagos → 1 pago; las dos respuestas tienen el mismo id | `persistencia_salida.txt` (1) |
| Repetición de la anulación | ANULADO, 1 evento → ANULADO, 1 evento; la segunda respuesta es 409 | `persistencia_salida.txt` (2) |
| Permanencia tras reinicio | Se detienen gunicorn y PostgreSQL y se vuelven a iniciar → `psql` y la API leen ANULADO con el motivo | `persistencia_salida.txt` (3) |
| TRUNCATE de la auditoría | 2 filas → 2 filas y error del disparador | `persistencia_salida.txt` (4), `truncate_antes.txt`, `truncate_despues.txt` |
