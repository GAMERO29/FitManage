# Ejercicio 5 · OpenAPI generado por IA para los endpoints reales

**Herramienta:** Claude (Anthropic), sesión nueva y sin contexto del proyecto. **Fecha:** 31/10/2026.

## Prompt

> Genera la especificación OpenAPI 3.0 en YAML de la API de un sistema de gestión de gimnasio con estos endpoints: iniciar sesión, registrar socio, consultar el estado de un socio por cédula, registrar pago, anular pago, reporte de ingresos entre dos fechas y próximos vencimientos. Usa JWT.

## Respuesta de la IA (sin modificar)

La especificación está completa en [`openapi-ia.yaml`](openapi-ia.yaml). El texto que la acompañaba:

> Aquí tienes la especificación OpenAPI 3.0 de tu API de gimnasio. Incluye autenticación JWT mediante el esquema `bearerAuth`, los modelos `Usuario`, `Socio` y `Pago`, y todos los endpoints solicitados. El endpoint `/socios/{cedula}` devuelve toda la información del socio, incluido su estado y fecha de vencimiento, para que la recepción tenga los datos completos. Para anular un pago puedes usar `POST /pagos/{id}/anular`, o `DELETE /pagos/{id}` si prefieres eliminarlo definitivamente. El reporte recibe el rango de fechas en el cuerpo de la petición.

## Lo que dicen los linters

- Redocly (`lint-redocly.txt`): **8 errores y 17 advertencias**. Los 8 errores son `security-defined`: el esquema `bearerAuth` existe en `components`, pero ninguna operación lo usa ni hay `security` global.
- Spectral (`lint-spectral.txt`): **26 advertencias**: faltan `operationId`, `tags`, descripciones y respuestas 4XX.

Ningún linter marcó lo más grave: que la consulta de recepción devuelve teléfono, dirección y fecha de nacimiento, que el login devuelve la contraseña, que hay un `DELETE` que borra pagos y que el reporte es un `GET` con cuerpo. Eso solo lo encontré leyendo el contrato con las reglas del negocio en la mano.

## Corrección

El contrato corregido es [`docs/api/openapi.yaml`](../../api/openapi.yaml), y las pruebas de `tests/contrato/test_openapi.py` impiden que estos errores vuelvan a entrar. La tabla de auditoría está en el Ejercicio 5 de la guía resuelta.
