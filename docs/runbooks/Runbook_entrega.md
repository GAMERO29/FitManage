# Runbook de entrega de una versión de FitManage

Guía II-05 (9/11/2026). Trabajo solo: ejecuto, reviso y decido yo. Lo que revisa algo distinto de mí está marcado como **[pipeline]**.

## Antes de integrar (candidata)

1. El PR pasa los 12 checks **[pipeline]** y la recomendación de la Guía II-04 no tiene condiciones abiertas que impidan desplegar.
2. Si el PR trae una migración: la ensayé en una copia con datos ficticios, hacia adelante y con una fila incoherente (`docs/guia-ii03/ensayo_migracion.sh`), y comprobé que la versión anterior funciona con el esquema nuevo. Si no es compatible hacia atrás, **no** se integra con despliegue automático: se sigue el procedimiento manual de abajo.
3. Ningún secreto en el PR **[pipeline: secretos, Trivy]**.

## Despliegue (automático al integrar en `main`)

4. **[pipeline]** CI construye la imagen una sola vez, corre la suite contra PostgreSQL 16 dentro de esa imagen y la publica en GHCR como `sha-<commit>`.
5. **[pipeline]** Despliegue pide a Render esa imagen exacta (Deploy Hook). Al arrancar, `docker/arrancar.sh` aplica `migrate` y después levanta gunicorn. Si la migración falla, el contenedor no arranca y Render sigue sirviendo la versión anterior.
6. **[pipeline]** `despliegue/verificar.py`: tres respuestas seguidas de `/api/v1/salud` con la versión nueva y una ruta protegida que sigue respondiendo 401. Si no lo logra en 10 minutos, el pipeline vuelve a la imagen estable anterior.

## Después del despliegue (yo)

7. Verificación funcional en el entorno local con el mismo commit y datos ficticios (`docs/guia-ii05/entrega_controlada.sh`, pasos 2 y 3). En producción **no** creo datos de prueba: la auditoría es de solo inserción y un evento de prueba quedaría para siempre.
8. En Grafana Cloud, durante 30 minutos: tasa de errores 5xx y p95 del recorrido de recepción contra la línea base (ADR N.° 14). **Detener o revertir** (criterio de esta guía) si se dispara la alerta de consumo del presupuesto de error, si los 5xx superan el 1 % de las peticiones durante 5 minutos o si el p95 de la consulta de estado pasa de 2 s.
9. Correr `docs/guia-ii05/coherencia_auditoria.sql` contra la base: debe devolver 0 filas. Si devuelve pagos sin evento, alguna versión sin auditoría escribió en la base (por ejemplo, después de volver a una imagen anterior a la 1.1.0) o hay un defecto.
10. Etiquetar la versión con el workflow **Release** (`release.yml`), que solo acepta un commit con despliegue exitoso.

## Revertir

- **Código:** volver a desplegar la imagen `sha-<commit estable>` por el Deploy Hook (`RENDER_DEPLOY_HOOK=… python -m despliegue.render ghcr.io/gamero29/fitmanage:sha-<commit>`). El workflow de Despliegue solo corre después de un CI exitoso en `main`, así que no sirve para elegir una versión vieja; el pipeline sí hace ese retroceso solo cuando la verificación falla.
- **Datos:** no se ejecuta una migración hacia atrás si borra datos (la 0003 borra la auditoría). Una restauración desde respaldo pierde todo lo posterior al respaldo: antes de hacerla hay que saber qué pagos y eventos se perderían y cómo se reconciliarían.
- **Respaldos:** la base gratuita de Render no tiene copias automáticas. Mientras no se cambie de plan (hito H1), el respaldo es un `pg_dump` manual por la *External Database URL*.
