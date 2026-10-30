# Prompt enviado a la IA (Ejercicio 5)

**Herramienta:** Claude (Anthropic), sesión de chat. **Fecha:** 30/10/2026.

**Datos enviados:** solo el fragmento ficticio de la guía (`legado.py`). No se envió código ni datos de FitManage, ni nombres, cédulas o teléfonos reales.

> Actúa como ingeniero de software senior. Refactoriza el siguiente código Python aplicando SOLID, en especial el principio de Inversión de Dependencias, para desacoplar la base de datos y la pasarela de pago. Mantén el mismo comportamiento y explica brevemente qué cambiaste.
>
> (se pegó el contenido de `legado.py`)

## Explicación que acompañó al código (`respuesta_ia.py`)

> 1. Creé tres abstracciones (`RepositorioZapatos`, `RepositorioVentas` y `PasarelaPago`) y el servicio `ServicioVentas` depende solo de ellas: así se cumple la Inversión de Dependencias y la variable global desaparece.
> 2. Las consultas ahora son parametrizadas (`%s`), lo que elimina la inyección SQL.
> 3. La API key de PayU se lee de la variable de entorno `PAYU_API_KEY`, de modo que ya no queda expuesta en el código.
> 4. El IVA se extrajo a una constante para facilitar su mantenimiento.
> 5. Con estos cambios el código queda libre de las vulnerabilidades originales y listo para producción.
