# Pruebas de carga (Guía 8, FPI-24, ADR N.° 08)

**Regla de oro: ninguna prueba de carga se ejecuta contra producción.** `consulta_estado.js` aborta si `BASE_URL` no es `127.0.0.1` o `localhost`, y `sembrar.py` se niega a escribir en una base que no sea local y termine en `_carga`.

## Entorno de carga

```bash
# 1. Base aparte, nunca la de desarrollo
createdb -O fitmanage fitmanage_carga
export DATABASE_URL=postgresql://fitmanage:CLAVE@127.0.0.1:5432/fitmanage_carga
python pruebas_carga/sembrar.py          # 2.000 socios y 20.000 pagos (QA-01), siempre los mismos

# 2. La aplicación como en el despliegue
export JWT_CLAVE=$(openssl rand -hex 32) DJANGO_SECRET_KEY=$(openssl rand -hex 32)
gunicorn config.wsgi --workers 2 --bind 127.0.0.1:8000

# 3. La prueba
k6 run pruebas_carga/consulta_estado.js                        # QA-01: 10 VUs, 10 minutos
k6 run -e PERFIL=exploracion pruebas_carga/consulta_estado.js  # margen: hasta 50 VUs
```

## Antes de guardar un resumen de k6

`--summary-export` incluye `setup_data`, y ahí va el token de acceso que `setup()` obtuvo. En la Guía 8 se subieron cinco resúmenes con ese token. Era de 15 minutos y estaba firmado con una clave del entorno de carga que ya no existe, así que no sirve para nada, pero era un token real dentro del repositorio. En la Guía 12 el job `secretos` lo detectó, se reemplazó por un texto y desde entonces el pipeline rechaza cualquier JWT nuevo en el repositorio (ADR N.° 12).

## Umbrales

| Umbral | Valor | De dónde sale |
| --- | --- | --- |
| `http_req_duration` p95 | < 2000 ms | RNF-01 y QA-01 |
| `http_req_failed` | 0 % | QA-01: «ninguna termina en error» |
| `checks` | 100 % | Cada respuesta es 200 y trae un estado válido |
| p95 de `consultarEstado` | < 300 ms | Alarma de ingeniería (ADR N.° 08): avisa antes de que la recepcionista lo note |

## Resultados (2/11/2026, k6 v1.5.0, gunicorn 2 workers, PostgreSQL 16, 2 núcleos compartidos)

| Corrida | Peticiones | p95 | Mediana | Errores | Evidencia |
| --- | --- | --- | --- | --- | --- |
| QA-01, conexión nueva por petición | 5.307 | 31,7 ms | 22,6 ms | 0 % | `docs/pruebas/carga/qa01-salida-k6.txt` |
| Exploración hasta 50 VUs | 13.206 | 37,8 ms | 24,0 ms | 0 % | `docs/pruebas/carga/exploracion-salida-k6.txt` |
| 3 min, 10 VUs, `CONN_MAX_AGE=0` | 1.485 | 29,9 ms | 22,5 ms | 0 % | `docs/pruebas/carga/conexiones-0s-resumen.json` |
| 3 min, 10 VUs, `CONN_MAX_AGE=60` | 1.505 | 11,8 ms | 8,8 ms | 0 % | `docs/pruebas/carga/conexiones-60s-resumen.json` |
| QA-01 con el ADR N.° 08 (`CONN_MAX_AGE=60`) | 5.377 | **13,5 ms** | 9,3 ms | 0 % | `docs/pruebas/carga/qa01-con-adr08-salida-k6.txt` |
