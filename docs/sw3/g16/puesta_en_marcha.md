# Procedimiento de puesta en marcha y recuperación · Guía 16 (ADR N.° 22)

El artefacto es siempre el mismo: el commit `X` y la imagen `ghcr.io/gamero29/fitmanage:sha-X` que CI construye, prueba y publica a partir de ese commit. Nada se vuelve a construir para desplegar (ADR N.° 11).

## A. En Render (nube pública, PaaS), el camino normal

1. Se fusiona un PR en `main`. El workflow **CI** construye la imagen `sha-X`, corre las pruebas dentro de ella y la publica en GHCR.
2. Con CI en verde, `deploy.yml` llama al Deploy Hook de Render con `imgURL=ghcr.io/gamero29/fitmanage:sha-X`. El hook es un secreto del environment `produccion` y nunca se imprime.
3. Render descarga la imagen y la arranca con `docker/arrancar.sh`, que aplica las migraciones, crea los planes y el primer administrador si no existen, y deja gunicorn en `$PORT` con 1 proceso y 4 hilos.
4. `despliegue/verificar.py` exige que `/api/v1/salud` responda 200 con la versión `X` tres veces seguidas y que `/api/v1/estados` siga pidiendo token.
5. Si pasa, la etiqueta `estable` se mueve a `sha-X`. **Si no pasa, el mismo job hace la reversión:** vuelve a desplegar `estable`, la verifica y deja la corrida en rojo.

**Evidencia en la nube.** Es la corrida 46081099053 del workflow *Despliegue*, del 27/11/2026, con el commit `2bd5e62`:

```
23:11:56 Render aceptó el despliegue de ghcr.io/gamero29/fitmanage:sha-2bd5e628b0c8… (HTTP 200)
23:11:56 Esperando: HTTP 200, versión en línea f69367a…        (5 veces, cada 10 s)
23:12:47 OK 1/3: versión 2bd5e628b0c8 en línea
23:13:07 OK 3/3: versión 2bd5e628b0c8 en línea
23:13:07 OK: /api/v1/estados sigue exigiendo token (401)
23:13:10 etiqueta estable → sha-2bd5e628…
```

Desde el hook hasta la primera respuesta de la versión nueva pasaron 51 s, y hasta la tercera verificación, 71 s. La reversión automática se ensayó en la Software II con la rama `simulacro/rollback-1` (corrida 41573794539, 3/11/2026). La imagen rota no quedó sana en 900 s, el job volvió a desplegar `estable` (`6432f55`) y esa versión respondió sana 21 s después del hook. El tiempo total de la reversión lo domina la espera de 15 minutos antes de declarar la falla.

## B. Desde cero en una cuenta nueva de Render (si se pierde el servicio)

1. Crear la base: *New → Postgres*, plan **0.1c-256mb** (US$6 al mes). No usar el plan Free para datos reales, porque vence a los 30 días y no tiene respaldos.
2. Crear el servicio: *New → Web Service → Existing image* con `ghcr.io/gamero29/fitmanage:estable`, instancia **0.5c-512mb** (US$7 al mes).
3. En *Environment*, cargar las variables de `variables.env.ejemplo`. `DATABASE_URL` es la *Internal Database URL* de la base del paso 1. Las dos claves se generan con `openssl rand -hex 32`.
4. Copiar el Deploy Hook del servicio al secreto `RENDER_DEPLOY_HOOK` del environment `produccion` en GitHub, y la URL pública a la variable `URL_PRODUCCION`.
5. Volver a correr la última corrida verde de *Despliegue*. Su verificación (A.4) es la prueba de salud.
6. Si hay datos que recuperar, restaurar el último respaldo (sección C) **antes** del paso 5.

## C. Recuperación de la base

| Caso | Cómo se recupera | RPO esperado |
| --- | --- | --- |
| Error de datos con la base en plan pago | *Recovery → Point-in-time*: Render crea una base nueva en el instante elegido (hasta 3 días atrás en Hobby). Se apunta `DATABASE_URL` a ella y se despliega. | Minutos |
| Base perdida o fuera de la ventana de PITR | `pg_restore --no-owner -d $DATABASE_URL respaldo.dump` del último `pg_dump` semanal guardado fuera de Render. Luego `migrate`, que no hace nada si el esquema ya está. | Hasta 7 días con un respaldo semanal; el plan B en papel cubre lo que falte |
| Base en plan Free (situación actual) | Solo existe el `pg_dump` que haga el equipo. Render no guarda nada. | Lo que haya pasado desde el último `pg_dump` manual |

## D. En el laboratorio (contenedor Linux local)

`docs/sw3/g16/despliegue_reproducible.sh 2bd5e62` hace los pasos de A y C con la misma versión que está en Render:

1. Saca el commit en un directorio aparte con `git worktree` y comprueba que no tenga cambios locales.
2. Crea una base PostgreSQL 16 nueva, migra, prepara el gimnasio y arranca gunicorn con el mismo comando de `arrancar.sh`.
3. Revisa la salud, corre el recorrido de 12 pasos y deja a Ana Prueba Demo con un pago vigente.
4. Saca un respaldo con `pg_dump -Fc` y, después, registra a Bruno Prueba Demo con su pago.
5. Borra la base (`DROP DATABASE`), restaura el respaldo y vuelve a arrancar.
6. Verifica la salud, los conteos, que Ana conserve su vigencia, que Bruno ya no exista (es lo que mide el RPO) y que la auditoría siga rechazando TRUNCATE.

El resultado de la corrida está en `despliegue_reproducible_salida.txt`.
