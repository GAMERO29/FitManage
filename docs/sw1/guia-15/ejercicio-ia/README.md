# Guía 15 (FPI-15) · YAML de CI generado por IA

- **IA:** Claude Haiku, con un prompt sin ningún secreto. Prompt y respuesta sin editar en esta carpeta; el YAML extraído es `ci-ia.yml.txt` y pasa `actionlint` sin errores (`actionlint-ia.txt`).

| Pregunta de la guía | Hallazgo |
| --- | --- |
| ¿Puso credenciales en texto plano? | **No las de Docker Hub:** usa `secrets.DOCKERHUB_USERNAME` y un *access token*, no la contraseña. **Sí dos de CI:** `POSTGRES_PASSWORD: postgres` y `DJANGO_SECRET_KEY: ci-clave-no-secreta`. Son de una base efímera, pero la regla de oro de la guía no tiene esa excepción; el pipeline real usa PostgreSQL con `trust` en localhost, sin contraseña. |
| ¿Usó bien las variables de entorno? | **No, y es el hallazgo más grave.** Definió `DB_NAME`, `DB_USER`, `DB_HOST`…, que FitManage no lee: el proyecto usa `DATABASE_URL`. Sin esa variable, `config/settings.py` usa SQLite. El job «Pruebas (Django 5.2 + PostgreSQL)» saldría en verde **sin tocar nunca PostgreSQL**. |
| Otros | Acciones sin fijar por SHA (`@v4`, `@v5`); la etiqueta `latest`; sin bloque `permissions`; ramas `develop`, que GitHub Flow no usa; instala `pytest` sin versión. `actionlint` no marca nada de esto. |

**Corrección.** El pipeline real es `.github/workflows/ci.yml`: `DATABASE_URL` explícita, acciones fijadas por SHA, permisos mínimos, la imagen etiquetada por commit y no `latest`, y nueve checks requeridos por la regla de `main`.
