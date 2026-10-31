# Catálogo de errores de la API

Todos los errores salen como `application/problem+json` (RFC 9457) con `type`, `title`, `status` y `codigo`. El `codigo` es estable: el cliente decide qué mostrar con él y no con el texto.

| Anclaje | `codigo` | HTTP | Cuándo |
| --- | --- | --- | --- |
| <a id="solicitud-invalida"></a>solicitud-invalida | `SOLICITUD_INVALIDA` | 400 | Falta un campo, sobra uno o alguno no cumple el formato. `errores` dice cuál. |
| <a id="no-autenticado"></a>no-autenticado | `NO_AUTENTICADO` | 401 | Falta el token, venció o la firma no es válida. |
| <a id="credenciales-invalidas"></a>credenciales-invalidas | `CREDENCIALES_INVALIDAS` | 401 | Correo o contraseña incorrectos (no se dice cuál). |
| <a id="sin-permiso"></a>sin-permiso | `SIN_PERMISO` | 403 | El rol no puede hacer esto (el entrenador en pagos, la recepcionista en reportes). Queda en la auditoría. |
| <a id="no-encontrado"></a>no-encontrado | `NO_ENCONTRADO` | 404 | No existe el socio, el plan o el pago. |
| <a id="documento-duplicado"></a>documento-duplicado | `DOCUMENTO_DUPLICADO` | 409 | Ya hay un socio con ese tipo y número (RN-01). |
| <a id="comprobante-duplicado"></a>comprobante-duplicado | `COMPROBANTE_DUPLICADO` | 409 | La referencia ya pertenece a un pago vigente (RN-06). |
| <a id="no-es-el-ultimo-pago"></a>no-es-el-ultimo-pago | `NO_ES_EL_ULTIMO_PAGO` | 409 | Se intentó anular un pago que no es el último vigente o que ya estaba anulado (RN-07). |
| <a id="cuenta-bloqueada"></a>cuenta-bloqueada | `CUENTA_BLOQUEADA` | 423 | 5 intentos fallidos; se desbloquea sola a los 15 minutos. |
| <a id="demasiadas-solicitudes"></a>demasiadas-solicitudes | `DEMASIADAS_SOLICITUDES` | 429 | Más de 60 solicitudes por minuto desde la misma IP. |
| <a id="correo-no-disponible"></a>correo-no-disponible | `CORREO_NO_DISPONIBLE` | 503 | El servidor SMTP no respondió al enviar el enlace de restablecimiento; la cuenta no cambia. |
| <a id="servicio-no-disponible"></a>servicio-no-disponible | `SERVICIO_NO_DISPONIBLE` | 503 | La base de datos no responde. |
