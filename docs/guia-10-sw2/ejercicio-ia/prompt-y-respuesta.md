# Ejercicio 5 · Dockerfile y docker-compose.yml generados por IA

**Herramienta:** Claude (Anthropic), en una conversación sin el repositorio. **Fecha:** 2/11/2026.

## Prompt

> Genera el Dockerfile y el docker-compose.yml para mi backend Django 5 (proyecto FitManage, settings en config.settings) con PostgreSQL. Quiero levantar todo con docker compose up.

## Respuesta de la IA (sin modificar)

Los dos archivos están en [`Dockerfile.ia.txt`](Dockerfile.ia.txt) y [`docker-compose.ia.yml.txt`](docker-compose.ia.yml.txt), con extensión `.txt` para que nadie los use por error. El texto que los acompañaba:

> Con estos dos archivos puedes levantar tu proyecto con `docker compose up --build`. Usé la imagen oficial `python:3.9`, que incluye todo lo necesario para compilar psycopg2, e instalé `gcc` y `libpq-dev` por si alguna dependencia lo requiere. El contenedor aplica las migraciones al iniciar. Monté el código como volumen para que veas los cambios sin reconstruir, y guardé los datos de PostgreSQL en `./data` para que no se pierdan. Recuerda cambiar la `SECRET_KEY` y la contraseña antes de pasar a producción.

## Auditoría y corrección

La tabla de hallazgos está en el Ejercicio 5 de la guía resuelta. El peso de la imagen que produce este Dockerfile se midió en CI junto con las demás (informe de contenedores). Los archivos corregidos son el [`Dockerfile`](../../../Dockerfile) y el [`docker-compose.yml`](../../../docker-compose.yml) de la raíz.
