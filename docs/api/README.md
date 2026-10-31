# API de FitManage (contrato Design-First)

El contrato [`openapi.yaml`](openapi.yaml) se escribió **antes** de los controladores (Guía 6, FPI-22). Desde la Guía 7 (FPI-23) las 13 operaciones están implementadas en `infraestructura/api/`, cada solicitud se valida contra el contrato con openapi-core y cada respuesta de las pruebas de integración también (`tests/apoyo_api.py`).

| Archivo | Qué es |
| --- | --- |
| [`openapi.yaml`](openapi.yaml) | Contrato OpenAPI 3.0.3 (versión 1.1.0): 13 operaciones en 6 contextos, seguridad JWT global y esquemas públicos sin datos sensibles. |
| [`FitManage.postman_collection.json`](FitManage.postman_collection.json) | 11 peticiones con 17 aserciones contra el mock de Prism. Contra Django las reemplazan las 75 pruebas de `tests/integracion/api/`. |
| [`../../vista-movil/pacts/`](../../vista-movil/pacts/) | Pact de la vista móvil (consumidor), verificado contra la API real en `tests/contrato/test_pact_proveedor.py`. |
| [`evidencia-newman.txt`](evidencia-newman.txt) | Salida de la última corrida local de la colección. |
| [`errores.md`](errores.md) | Catálogo de códigos de error (`problem+json`). |
| [`.spectral.yaml`](.spectral.yaml) | Reglas de Spectral (`spectral:oas`). |

## Endpoints

| Verbo | URI | Contexto | Códigos | JWT |
| --- | --- | --- | --- | --- |
| GET | `/salud` | Sistema | 200, 429, 503 | No (monitoreo del PaaS, sin datos) |
| POST | `/auth/token` | Acceso del personal | 200, 400, 401, 423, 429 | No (es el que lo entrega) |
| POST | `/auth/renovacion` | Acceso del personal | 200, 401 | No: cookie de renovación `HttpOnly` |
| POST | `/personal/{usuarioId}/restablecimiento` | Acceso del personal | 202, 401, 403, 404, 503 | Sí, administrador (única dependencia externa: SMTP) |
| POST | `/socios` | Socios | 201, 400, 401, 403, 409 | Sí |
| GET | `/estados` | Recepción (OHS) | 200, 400, 401, 403 | Sí |
| GET | `/estados/{tipoDocumento}/{numeroDocumento}` | Recepción (OHS) | 200, 400, 401, 403, 404 | Sí |
| GET | `/planes` | Membresías y cobros | 200, 401, 403 | Sí |
| POST | `/pagos` | Membresías y cobros | 201, 400, 401, 403, 404, 409 | Sí |
| PATCH | `/pagos/{pagoId}` | Membresías y cobros | 200, 400, 401, 403, 404, 409 | Sí, rol administrador |
| GET | `/reportes/ingresos` | Reportes | 200, 400, 401, 403 | Sí, rol administrador |
| GET | `/vencimientos` | Recordatorios | 200, 400, 401, 403 | Sí |

Auditoría no expone endpoints: solo recibe eventos dentro de la misma transacción (ADR N.° 05); esos eventos todavía no se guardan (DT-14). El 429 está documentado pero aún no se emite (DT-13). En todas las operaciones con JWT, el rol Entrenador recibe 403.

## Cómo validarlo

```bash
npx @redocly/cli@1.34.22 lint docs/api/openapi.yaml
npx @stoplight/spectral-cli@6.17.0 lint docs/api/openapi.yaml --ruleset docs/api/.spectral.yaml --fail-severity=warn
npx @stoplight/prism-cli@5.14.2 mock docs/api/openapi.yaml -p 4010   # en otra terminal
npx newman@6.2.3 run docs/api/FitManage.postman_collection.json
pytest tests/contrato                                                 # regla de oro de la guía
```

El trabajo `contrato-api` del flujo `Calidad` corre los cuatro primeros pasos en cada push. Las pruebas de `tests/contrato/` revisan la regla de oro de la guía: ningún endpoint sin seguridad declarada salvo los justificados, ningún esquema con datos sensibles salvo el teléfono de los recordatorios, ningún `GET` con cuerpo y la anulación como `PATCH`.

## Privacidad de las respuestas

- `EstadoPublico` (lo que consulta la recepción y guarda la caché del celular) trae nombre corto («Ana P.»), documento enmascarado («CC ******3456»), estado y fechas. No trae teléfono, documento completo, pagos ni montos.
- `SocioRegistrado` tampoco repite el documento ni el teléfono que se acaban de enviar.
- `Vencimiento` es el único que trae el teléfono, porque sin él no se puede armar el recordatorio por WhatsApp (RF-06), que es una finalidad aceptada en la autorización de datos.
- `ReporteIngresos` solo trae totales.
