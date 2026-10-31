# Estrategia de pruebas (FPI-23, ADR N.° 07)

Regla de oro: **ninguna prueba de integración escribe en la base de desarrollo**. pytest-django crea una base nueva para la corrida y la destruye al final; `tests/integracion/api/test_api_sistema.py::test_la_base_de_estas_pruebas_es_efimera` lo comprueba.

## La pirámide de FitManage hoy

| Nivel | Dónde | Pruebas | Tiempo | Qué prueba | Dobles |
| --- | --- | --- | --- | --- | --- |
| E2E / interfaz | — | 0 | — | Todavía no hay plantillas Django; el prototipo se revisa a mano. | — |
| Aceptación (UAT) | `tests/aceptacion/` (Gherkin + pytest-bdd) | 9 | 1,8 s | PA-01, 02, 03, 05, 07, 08, 09, 10 y 11 del DDS, contra la API real. | Reloj |
| Contrato | `tests/contrato/` y `vista-movil/test/` | 12 + 4 | 2,8 s | Regla de oro del contrato OpenAPI (11) y verificación Pact del proveedor (1); 4 interacciones del consumidor en Node. | Token de ejemplo del consumidor |
| Integración | `tests/integracion/` | 95 | 4,8 s | 75 de la API (HTTP → caso de uso → ORM → base), 19 de repositorios ORM y 1 de concurrencia en PostgreSQL (QA-05). | Reloj y SMTP |
| Unitarias | `tests/nucleo/` | 87 | 0,1 s sin Django | Dominio y casos de uso con repositorios en memoria. | Repositorios en memoria |

Total: 203 pruebas en Python (202 en SQLite, porque la de concurrencia solo corre en PostgreSQL), más 4 del consumidor Pact. Cobertura de líneas y ramas: 100 %.

## Qué se reemplaza y qué no

| Frontera | En producción | En las pruebas |
| --- | --- | --- |
| Hora | `RelojBogota` | `RelojFijo` inyectado en `infraestructura/api/contenedor.reloj` |
| Correo (restablecer clave) | SMTP del hosting vía `CorreoDjango` | backend `locmem` de Django; `tests/correo_caido.py` simula el servidor caído |
| Base de datos | PostgreSQL 16 | base efímera de pytest-django (SQLite en memoria o `test_fitmanage`) |
| Dominio, casos de uso, repositorios, controladores, contrato | reales | **reales: nunca se mockean** |

## Cómo correr cada nivel

```bash
pytest tests/nucleo -p no:django          # unitarias, sin Django
pytest tests/integracion                  # integración (SQLite en memoria)
DATABASE_URL=postgresql://... pytest      # todo contra PostgreSQL, incluida QA-05
pytest tests/aceptacion                   # escenarios PA del DDS
pytest tests/contrato                     # contrato OpenAPI + verificación Pact del proveedor
cd vista-movil && npm ci && npm run test:pact   # consumidor Pact (regenera el pact)
```
