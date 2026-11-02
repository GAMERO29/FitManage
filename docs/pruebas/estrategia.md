# Estrategia de pruebas (FPI-23 y FPI-24, ADR N.° 07 y 08)

Regla de oro: **ninguna prueba de integración escribe en la base de desarrollo**. pytest-django crea una base nueva para la corrida y la destruye al final; `tests/integracion/api/test_api_sistema.py::test_la_base_de_estas_pruebas_es_efimera` lo comprueba.

## La pirámide de FitManage hoy

| Nivel | Dónde | Pruebas | Tiempo | Qué prueba | Dobles |
| --- | --- | --- | --- | --- | --- |
| E2E / interfaz | — | 0 | — | Todavía no hay plantillas Django; el prototipo se revisa a mano. | — |
| Aceptación (UAT) | `tests/aceptacion/` (Gherkin + pytest-bdd) | 9 | 1,8 s | PA-01, 02, 03, 05, 07, 08, 09, 10 y 11 del DDS, contra la API real. | Reloj |
| Contrato | `tests/contrato/` y `vista-movil/test/` | 12 + 4 | 2,8 s | Regla de oro del contrato OpenAPI (11) y verificación Pact del proveedor (1); 4 interacciones del consumidor en Node. | Token de ejemplo del consumidor |
| Integración | `tests/integracion/` | 95 | 4,8 s | 75 de la API (HTTP → caso de uso → ORM → base), 19 de repositorios ORM y 1 de concurrencia en PostgreSQL (QA-05). | Reloj y SMTP |
| Unitarias | `tests/nucleo/` | 94 | 0,1 s sin Django | Dominio y casos de uso con repositorios en memoria. | Repositorios en memoria |

Total: 210 pruebas en Python (209 en SQLite, porque la de concurrencia solo corre en PostgreSQL), más 4 del consumidor Pact. Cobertura de líneas y ramas: 100 %. Las 7 unitarias nuevas son las del recordatorio de WhatsApp, escritas con TDD en la Guía 8 (commits `b9b5a59`, `bd67f56` y `825db00`).

## Regresión (Guía 8)

Toda la suite es la suite de regresión: corre en cada push a `main` y en cada Pull Request, y no se une un PR en rojo. Corre dos veces y en dos órdenes distintos: en paralelo con `pytest-xdist` (`-n auto`, SQLite) en el trabajo `pruebas-y-analisis`, y en serie contra PostgreSQL 16 en el trabajo `contenedores`. Con xdist cada proceso tiene su propia base (`test_fitmanage_gw0`, `_gw1`…), y eso destapó que la prueba de la regla de oro esperaba un solo nombre de base.

## Rendimiento (Guía 8, ADR N.° 08)

`pruebas_carga/` tiene el script de k6 de la consulta de recepción (QA-01) y la siembra de la base de carga. No corre en CI: necesita un servidor levantado y 10 minutos. Se corre a mano antes de cada entrega y en staging antes del piloto. Resultados y comandos en `pruebas_carga/README.md`.

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
pytest -n auto                            # toda la suite en paralelo, como en CI
DATABASE_URL=postgresql://... pytest      # todo contra PostgreSQL, incluida QA-05
pytest tests/aceptacion                   # escenarios PA del DDS
pytest tests/contrato                     # contrato OpenAPI + verificación Pact del proveedor
cd vista-movil && npm ci && npm run test:pact   # consumidor Pact (regenera el pact)
```
