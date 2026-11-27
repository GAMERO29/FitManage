# Auditoría de IA · Guía 09 (herencia contra composición)

**Prompt.** «Diseña con herencia las formas de enviar correo de FitManage: SMTP en producción,
consola en desarrollo y una variante que no envíe nada para las pruebas.» Sin datos ni secretos.

**Salida relevante.** [`propuesta_ia.py`](propuesta_ia.py): una clase base `Notificador` con un
método plantilla y tres subclases.

## Precondiciones y poscondiciones de cada subtipo

| Subtipo | Contrato de `CorreoSaliente` | Resultado ([`verificacion_ia.txt`](verificacion_ia.txt)) |
|---|---|---|
| `NotificadorSMTP` | Acepta cualquier dirección con «@» | **Refuerza la precondición:** solo acepta `@gimnasio.co`. Un consumidor que funciona con la base deja de funcionar con este subtipo. |
| `NotificadorNulo` | Si retorna, el mensaje salió | **Debilita la poscondición:** devuelve `True` sin enviar. Es el «éxito falso» del caso de la ferretería. |
| `NotificadorConsola` | Destinatario inválido → error | Acepta un destinatario vacío y devuelve `True`. |
| Base `Notificador` | — | Mezcla dos razones de cambio: el formato del mensaje (`formatear`) y la entrega. Cambiar el texto obliga a tocar la jerarquía. |

## ¿La herencia es adecuada aquí?

No. Las variantes no comparten comportamiento que valga la pena heredar; solo comparten el
contrato. En FitManage la variación ya está resuelta por composición: `CorreoDjango` es el único
adaptador y lo que cambia es el backend de Django que se configura (`EMAIL_BACKEND`): SMTP en
producción, memoria en pruebas y `CorreoCaido` o `CorreoQueNoEntrega` para simular fallas. El
doble `CorreoEnMemoria` no descarta mensajes: los guarda para que la prueba los revise.

## Lo que la auditoría destapó en nuestro propio código

Al pasar la misma prueba de contrato por todas las variantes salieron 7 fallas, todas «éxito
falso» ([`contrato_antes.txt`](contrato_antes.txt)):

- `CorreoDjango` ignoraba el número que devuelve `send_mail`. Con un servidor que no entrega nada,
  la API respondía **202 «enviadoA»** con cero mensajes enviados.
- Ni el adaptador ni el doble revisaban el destinatario: con `""` el doble lo «enviaba».

Corrección: la precondición y la poscondición quedan escritas en el puerto, `exigir_destinatario`
es común a las variantes, `CorreoDjango` exige `send_mail(...) == 1` y una regresión de la API
comprueba el 503 ([`contrato_despues.txt`](contrato_despues.txt)).

**Limitación.** La misma sesión generó y auditó la propuesta. En producción no hay SMTP (DT-26),
así que la corrección se probó con backends de Django que simulan cada caso.
