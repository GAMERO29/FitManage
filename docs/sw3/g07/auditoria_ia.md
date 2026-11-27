# Auditoría de IA · Guía 07 (inversión de dependencias)

**Prompt.** «Refactoriza `infraestructura/api/autenticacion.py` de FitManage aplicando inversión de
dependencias: que no use `UsuarioModelo` directamente sino un puerto, con un doble en memoria para
las pruebas.» Material: solo el archivo, sin datos de personas ni secretos.

**Salida relevante.** Copiada en [`propuesta_ia.py`](propuesta_ia.py): un puerto `CuentaRepositorio`
con `por_correo` y `guardar`, un doble `CuentasEnMemoria` y el cambio de `select_for_update()` por
`por_correo(...)`.

## Qué revisé y qué encontré

| Afirmación o pieza | Criterio | Resultado |
|---|---|---|
| El puerto «aísla» al caso de uso del ORM | Los tipos de la firma | **Falso.** `por_correo` devuelve `UsuarioModelo`: el puerto filtra el tipo del motor. Quien lo consuma sigue atado a Django y al campo `clave_hash`. |
| El doble sirve para las pruebas | La misma cláusula que cumple el adaptador real | **Falso.** El doble busca el correo tal cual; la base busca con `correo__iexact` y `test_el_correo_no_distingue_mayusculas` lo exige. Con el doble, una prueba de login con mayúsculas daría 401 y con la base, 200. [`verificacion_ia.txt`](verificacion_ia.txt) |
| `por_correo` reemplaza la consulta | Comportamiento ante dos intentos al tiempo | **Se pierde el bloqueo de fila.** La consulta original usa `select_for_update()`; sin él, dos intentos fallidos concurrentes pueden leer el mismo contador y el quinto intento de RF-09 no bloquea. La propuesta no lo menciona. |

## Corrección

- El doble se corrige con la llave en `casefold()` y la verificación pasa (ver `verificar_propuesta.py`).
- No adopté el puerto de cuentas en esta guía. El problema real que tenía `autenticacion.py` era más
  pequeño: importaba la función privada `_a_usuario` de `repositorios.py`. Eso sí se corrigió
  (`infraestructura/persistencia/mapeo.py`) y lo vigila `test_ningun_modulo_importa_nombres_privados_de_otro`.
- Un puerto de cuentas queda priorizado en la ficha con sus dos condiciones: devolver un tipo del
  dominio (correo, rol, intentos, bloqueo; nunca el hash fuera del adaptador) y declarar que la
  lectura bloquea la cuenta dentro de la transacción.

**Limitación.** La misma sesión de IA generó y auditó la propuesta. Las tres observaciones se
apoyan en una prueba o en una línea del código, no en la opinión de quien audita.
