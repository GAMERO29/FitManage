# Ejercicio 5 · Ingeniería inversa de un fragmento legacy con IA, y su auditoría

- **Fragmento:** `registrar_pago` y `_respuesta_guardada` de `infraestructura/api/vistas.py`, con el modelo `IdempotenciaModelo` (el código más antiguo y más delicado del sistema: un pago y su idempotencia en la misma transacción).
- **Asistente:** Claude Haiku, sin herramientas ni acceso al repositorio, como lo usaría un estudiante en un chat.
- **Prompt:** [`prompt.txt`](prompt.txt), tal cual se envió.
- **Respuesta:** [`respuesta-ia.md`](respuesta-ia.md), sin editar.

## Cómo se auditó

Ninguna afirmación de la IA se aceptó por leerla. Cada una se probó contra el sistema real:

1. Una sonda de pruebas contra la API con el código actual, para comprobar los «problemas» que la IA dijo encontrar.
2. El código de la IA aplicado tal cual en una copia aparte del repositorio (worktree), con su migración generada por `makemigrations`, y la suite completa encima.
3. La misma copia con un único arreglo, para ver qué quedaba detrás del primer error.

## Resultado, afirmación por afirmación

| Lo que dijo la IA | Verificación | Veredicto |
| --- | --- | --- |
| «La clave es global, no por usuario»: otra persona con la misma clave recibe el pago ajeno. | Carlos reenvió la clave de Laura con otro socio: 201, `Idempotent-Replayed: true`, `registradoPor: Laura`, y su pago no se registró. | **Cierto.** Queda como DT-23 (hito H2), con la prueba `test_la_misma_clave_de_otra_persona_no_repite_su_pago` en `xfail(strict=True)`. |
| «No se verifica que el cuerpo coincida». | La misma clave con otro socio devuelve el pago anterior. | **Cierto.** Mismo ítem DT-23. |
| «Entradas inválidas producen errores 500» (UUID, tipo de documento, campos faltantes). | `Idempotency-Key: abc` → 400 `SOLICITUD_INVALIDA`; `tipoDocumento: XX` → 400; sin `planId` → 400. El validador del contrato OpenAPI rechaza la petición antes de llegar a la vista. | **Falso.** La IA no veía el contrato. Queda la prueba `test_idempotency_key_que_no_es_uuid_es_400_no_500`. |
| «Sin caducidad, la tabla crece sin límite». | Cierto, pero a este volumen (un gimnasio, decenas de pagos al día) son unos pocos miles de filas al año. | Cierto e irrelevante hoy. No entra al roadmap. |

## Qué pasó con su código

**¿Mantuvo la integridad transaccional?** Sí. Conserva el `atomic()` externo con el *savepoint* interno: si el pago falla, la reserva de la clave se deshace y se puede reintentar. Es lo único que la refactorización respetó por completo.

**¿Alteró la lógica de negocio?** Sí, en cuatro puntos, y ninguno lo anunció como cambio de comportamiento:

1. **Rompió todos los pagos.** Asignó `request.usuario` (una entidad del dominio) a una llave foránea de Django, que exige una instancia de `UsuarioModelo`. El código original usaba `usuario_id=request.usuario.id`. Resultado: **14 pruebas fallidas**, entre ellas PA-02, PA-03, PA-09 y PA-11, todas con `ValueError` y un 500 en `POST /pagos` (`evidencia/ia-codigo-tal-cual.txt`). La IA lo escribió en sus supuestos («existen tal como en tu código») sin mirar cómo se usaban.
2. **Cambió el contrato de la API.** Inventó respuestas 422 y 409 que no existen en `openapi.yaml`, con un formato `{"error": "..."}` en lugar del problem+json con `codigo` que usa toda la API. Con el primer error corregido, la suite pasa completa, pero solo porque ninguna prueba recorre esos caminos nuevos; una sonda con la misma clave y otro cuerpo hace fallar al validador: `ResponseNotFound: Unknown response http status: 422` (`evidencia/ia-codigo-con-fk-corregida.txt`).
3. **Exponía detalles internos.** `PeticionInvalida(f"Datos de pago inválidos: {exc}")` devuelve el texto de la excepción de Python al cliente.
4. **Borraba la tabla.** La migración que genera su modelo es `CreateModel RegistroIdempotencia` + `DeleteModel IdempotenciaModelo` (`evidencia/ia-migracion-generada.py.txt`): cambia de nombre la tabla y descarta los registros de idempotencia vigentes. Un doble clic justo durante el despliegue registraría dos pagos.

**¿Sugirió herramientas con licencias restrictivas?** No. SonarQube Community Build es LGPL-3.0 y SonarCloud es gratis para repositorios públicos (FitManage ya la usa en el check `analisis`). Ruff y Radon son MIT y Bandit es Apache-2.0. Lo que sí omitió es que el *scanner* necesita un token y que la edición Community no analiza ramas ni PR: para eso está SonarCloud.

## Corrección

No se adoptó el código de la IA. Se tomaron sus dos hallazgos ciertos y se convirtieron en deuda registrada, con una prueba que falla a propósito hasta que se paguen; el falso se convirtió en una prueba de regresión. El arreglo de DT-23 va en el hito H2 y empieza por el contrato: primero se documenta en `openapi.yaml` la respuesta para «clave usada con otro cuerpo», en formato problem+json, y después se cambia el código, con migración que conserve los registros.
