# Pipeline `CI` y Quality Gate (Guía 9, FPI-25, ADR N.° 09)

Workflow: [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml). Corre en cada Pull Request, en cada push a `main` y en cada etiqueta `vX.Y.Z`.

```
linter ──► pruebas ──► analisis (SonarCloud, espera el Quality Gate)
               └─────► artefacto (imagen → suite en PostgreSQL → humo k6 → GHCR solo en main)
contrato-api (en paralelo: OpenAPI, Prism, Postman y Pact)
```

## Quality Gate

| Capa | Criterio | Umbral | Dónde |
| --- | --- | --- | --- |
| Pipeline | Estilo y errores | 0 hallazgos de ruff | `linter` |
| Pipeline | Seguridad del código | 0 hallazgos de bandit | `linter` |
| Pipeline | Complejidad | Ningún bloque con complejidad ciclomática > 10 | `linter` |
| Pipeline | Dependencias | 0 vulnerabilidades conocidas (pip-audit) | `linter` |
| Pipeline | Regresión | 100 % de las pruebas en verde, en paralelo y contra PostgreSQL 16 | `pruebas`, `artefacto` |
| Pipeline | Cobertura de todo el código | Líneas y ramas ≥ 95 % | `pruebas` |
| Pipeline | Rendimiento (humo) | p95 < 2 s, 0 % de errores; alarma p95 < 300 ms | `artefacto` |
| SonarCloud | «Sonar way» sobre el código nuevo | Calificación A en fiabilidad, seguridad y mantenibilidad; hotspots revisados al 100 %; cobertura ≥ 80 %; duplicación ≤ 3 % | `analisis` |

El plan gratuito de SonarCloud no permite editar el Quality Gate, por eso el umbral propio del equipo (95 % sobre todo el código, no solo el nuevo) vive en la capa del pipeline.

## Qué hace que la puerta bloquee de verdad

1. **La regla de `main`** ([`ruleset-main.json`](ruleset-main.json), importada en *Settings → Rules → Rulesets*): exige PR y los cinco checks en verde, sin lista de excepciones.
2. **Ningún paso de la puerta tiene `continue-on-error`**, y `analisis` falla si falta `SONAR_TOKEN` en lugar de saltarse.
3. **`sonar.qualitygate.wait=true`**: el job no termina hasta que SonarCloud da su veredicto, y si es «Failed» queda en rojo.

## Secretos

| Secreto | Dónde vive | Quién lo usa |
| --- | --- | --- |
| `SONAR_TOKEN` | *Settings → Secrets and variables → Actions* | `analisis` |
| `GITHUB_TOKEN` | Lo crea GitHub en cada corrida | `artefacto`, solo para publicar en GHCR desde `main` |
| `JWT_CLAVE`, `DJANGO_SECRET_KEY` del humo de k6 | Se generan con `openssl rand` en la corrida y se enmascaran | `artefacto` |

PostgreSQL del runner usa `POSTGRES_HOST_AUTH_METHOD: trust`: es una base efímera que solo escucha en el localhost del runner, así que no hay ninguna contraseña que escribir en el YAML.

## Artefacto inmutable

`ghcr.io/gamero29/fitmanage:sha-<commit completo>` se publica solo después de que esa misma imagen pasó la suite contra PostgreSQL 16 y el humo de k6; con una etiqueta `vX.Y.Z` se publica además `X.Y.Z`. El resumen de la corrida muestra el digest. Para desplegar se usa esa etiqueta o el digest; nunca se reconstruye.
