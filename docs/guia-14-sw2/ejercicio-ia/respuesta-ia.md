<!-- Respuesta de la IA del Ejercicio 5 de la Guía 14, copiada sin modificar. -->

# Runbook de contingencia: "la base de datos no responde" (FitManage)

**Stack:** API Django + PostgreSQL en Render.
**Alcance:** diagnóstico y recuperación de la alerta. Las causas de fondo se revisan después, en el post-incidente.

> Nota: este runbook se escribió desde mi conocimiento general, sin consultar la documentación actual de Render. Antes de usarlo en producción, confirma en la documentación de Render para tu plan: si existe la opción de reinicio para la base de datos, la retención de backups y si hay point-in-time recovery. Ajusta también los nombres de servicios y las rutas a los de tu proyecto.

---

## 0. Variables y accesos previos

Ten a mano:

- Dashboard de Render: servicio web de la API y servicio de PostgreSQL.
- **External Database URL** de la base de datos (en la pestaña *Connections* de PostgreSQL).
- Acceso a la pestaña **Shell** del servicio web (o SSH, si está habilitado).
- Un terminal local con `psql` instalado.

En tu terminal local, define la URL (no la pegues en chats ni en commits):

```bash
export DATABASE_URL="postgresql://USUARIO:CLAVE@HOST.render.com:5432/NOMBRE_DB?sslmode=require"
```

Verifica que `psql` esté disponible:

```bash
psql --version
```

---

## 1. Clasificación y primeros 5 minutos

| Señal | Severidad | Acción |
|---|---|---|
| Errores 5xx en toda la API y la DB no acepta conexiones | SEV-1 | Escalar de inmediato, seguir este runbook |
| Lentitud severa, timeouts parciales | SEV-2 | Diagnóstico completo (secciones 2 y 3) |
| Alerta aislada que se resuelve sola | SEV-3 | Registrar y revisar en el post-incidente |

Registra la hora de inicio del incidente y quién lo atiende.

---

## 2. Diagnóstico

### Paso 2.1: Confirmar que la alerta es real

Desde tu terminal local:

```bash
psql "$DATABASE_URL" -c "SELECT now() AS hora_servidor, version();"
```

- **Si conecta:** la base responde desde fuera. El problema puede estar en la red interna, en la app o en el pool de conexiones. Continúa con el paso 2.2.
- **Si no conecta** (timeout, `connection refused`, `password authentication failed`, `could not translate host name`):
  - `password authentication failed`: la credencial cambió o se rotó. Ve a la sección 3.F.
  - `could not translate host name` o `connection refused`: la instancia puede estar caída o en mantenimiento. Ve a la sección 3.D.
  - `timeout`: revisa que la IP local no esté bloqueada por la lista de acceso de la base (si tu plan la usa) y continúa con el paso 2.2.

Revisa también en el dashboard de Render el estado de la instancia de PostgreSQL (Available, Deploying, Unhealthy, etc.) y sus métricas de CPU, memoria, conexiones y disco.

### Paso 2.2: Verificar la conectividad desde la app

En la pestaña **Shell** del servicio web de la API:

```bash
pwd
echo "$DATABASE_URL" | sed -E 's#://[^@]*@#://***@#'   # muestra la URL sin credenciales
python manage.py check --database default
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('CONEXION OK')"
```

- Si `check` falla o `ensure_connection` lanza `OperationalError`, el problema está entre la app y la base. Revisa la variable `DATABASE_URL` (paso 3.F) y el paso 2.3.
- Si conecta, la base responde y el problema probablemente es de saturación o de consultas bloqueadas.

### Paso 2.3: Revisar conexiones y saturación

Conéctate con `psql` local y ejecuta:

```sql
-- Límite del servidor y uso actual
SHOW max_connections;

SELECT state, count(*)
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state
ORDER BY count(*) DESC;
```

Interpretación:

- Muchas conexiones en `idle`: el pool o `CONN_MAX_AGE` están mal configurados, o hay muchos workers. Ve a la sección 3.A.
- Muchas en `active` con consultas largas: hay consultas lentas o bloqueadas. Ve al paso 2.4.
- Muchas en `idle in transaction`: la app abre transacciones y no las cierra. Ve a la sección 3.B.
- Total cercano a `max_connections`: saturación. Ve a la sección 3.A.

Detalle de sesiones activas:

```sql
SELECT pid, usename, application_name, client_addr, state,
       now() - state_change AS en_estado_desde,
       left(query, 150) AS consulta
FROM pg_stat_activity
WHERE datname = current_database()
  AND state <> 'idle'
ORDER BY en_estado_desde DESC;
```

### Paso 2.4: Revisar transacciones largas y bloqueos

Transacciones abiertas más de unos segundos:

```sql
SELECT pid, usename, state,
       now() - xact_start AS duracion_tx,
       wait_event_type, wait_event,
       left(query, 150) AS consulta
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
  AND datname = current_database()
ORDER BY duracion_tx DESC
LIMIT 20;
```

Sesiones bloqueadas y quién las bloquea:

```sql
SELECT pid AS bloqueada,
       pg_blocking_pids(pid) AS bloqueada_por,
       now() - query_start AS esperando_desde,
       left(query, 150) AS consulta_bloqueada
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;
```

Si aparece un bloqueador con una consulta de `ALTER TABLE`, `CREATE INDEX`, `VACUUM FULL` o una migración, es muy probable que la causa sea una migración o un mantenimiento. Ve a la sección 3.E.

### Paso 2.5: Revisar disco, tamaño y logs

Tamaño de la base:

```sql
SELECT pg_size_pretty(pg_database_size(current_database())) AS tamano_db;

SELECT relname AS tabla,
       pg_size_pretty(pg_total_relation_size(relid)) AS tamano_total
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 10;
```

En Render, revisa:

- **Métrica de disco** de la instancia de PostgreSQL. Si está cerca del 100 %, ve a la sección 3.C.
- **Logs** de la base y del servicio web. Busca `FATAL`, `too many clients`, `out of memory`, `disk full`, `deadlock detected`, `statement timeout`.
- **Eventos recientes** en el servicio web: despliegues, cambios de variables de entorno, reinicios.

### Paso 2.6: Revisar despliegues recientes

Si la alerta empezó después de un despliegue o de una migración:

```bash
# En la Shell del servicio web
python manage.py showmigrations | grep "\[ \]"   # migraciones pendientes
git log --oneline -5                              # si el código está versionado en el contenedor
```

Anota el commit desplegado. Es el candidato principal para rollback (sección 3.E).

---

## 3. Árbol de decisión y recuperación

Elige la rama que coincida con el diagnóstico. Antes de cualquier acción destructiva, toma un respaldo (paso 3.0).

### 3.0 Respaldo previo (obligatorio antes de acciones de riesgo)

```bash
pg_dump "$DATABASE_URL" -Fc -f "backup_fitmanage_$(date +%Y%m%d_%H%M).dump"
ls -lh backup_fitmanage_*.dump
```

Si `pg_dump` falla por versión, instala un cliente de PostgreSQL igual o mayor al servidor (`psql --version` y revisa la versión en Render).

### 3.A Saturación de conexiones (`too many clients`, conexiones cerca de `max_connections`)

**Causa típica:** demasiados workers de Gunicorn, pool sin límite o `CONN_MAX_AGE` mal configurado. La regla práctica es:

> conexiones ≈ instancias × workers × (conexiones por worker) + tareas en segundo plano + sesiones administrativas

**Mitigación inmediata:**

1. Cierra las conexiones inactivas de la aplicación (solo del usuario de la app, no de sistema):

   ```sql
   SELECT pid, usename, now() - state_change AS inactiva_desde
   FROM pg_stat_activity
   WHERE datname = current_database()
     AND state = 'idle'
     AND pid <> pg_backend_pid()
     AND now() - state_change > interval '10 minutes';
   ```

   Revisa el resultado y, si todo es del usuario de la aplicación, ejecuta:

   ```sql
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE datname = current_database()
     AND state = 'idle'
     AND pid <> pg_backend_pid()
     AND usename = 'NOMBRE_USUARIO_APP'
     AND now() - state_change > interval '10 minutes';
   ```

   La aplicación reabrirá sus conexiones. Es esperable un pico breve de latencia.

2. Reinicia el servicio web desde el dashboard (*Manual Deploy > Restart* o equivalente) para liberar los pools.

3. Si la saturación se repite, reduce workers temporalmente. En el comando de inicio del servicio (`Start Command`):

   ```bash
   gunicorn fitmanage.wsgi:application --workers 2 --threads 2 --timeout 30 --bind 0.0.0.0:$PORT
   ```

   Ajusta la cantidad según el límite de conexiones de tu plan.

**Mitigación de configuración** (para el despliegue siguiente, en `settings.py`):

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DB_NAME"],          # o dj_database_url si ya lo usas
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ["DB_HOST"],
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": 600,                     # reutilizar conexiones 10 min
        "CONN_HEALTH_CHECKS": True,              # descarta conexiones muertas (Django 4.1+)
        "OPTIONS": {
            "sslmode": "require",
            "options": "-c statement_timeout=30000 -c idle_in_transaction_session_timeout=60000",
        },
    }
}
```

Los dos timeouts de `options` cortan consultas de más de 30 s y transacciones ociosas de más de 60 s. Ajústalos a los tiempos reales de tu app.

### 3.B Transacciones abiertas o bloqueos por consultas largas

**Cancelar la consulta** (suave, la sesión sigue viva):

```sql
SELECT pg_cancel_backend(PID_AQUI);
```

**Terminar la sesión** (dura, solo si la cancelación no funciona en unos segundos):

```sql
SELECT pg_terminate_backend(PID_AQUI);
```

Reglas:

- Confirma el `pid` con el paso 2.4 antes de ejecutar.
- No termines procesos de sistema ni de replicación.
- Si la misma consulta reaparece, búscala en el código de la app (por ejemplo, un endpoint sin paginación o un `select_for_update` sin `transaction.atomic` correcto) y corrígela después.

Para sesiones `idle in transaction` antiguas:

```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = current_database()
  AND state = 'idle in transaction'
  AND usename = 'NOMBRE_USUARIO_APP'
  AND now() - state_change > interval '5 minutes';
```

### 3.C Disco lleno o casi lleno

1. Libera espacio sin borrar datos de negocio: elimina logs o tablas temporales que sean tuyas y verifica que puedas recuperarlas.
2. Si la tabla creció por una tarea, pausa esa tarea primero.
3. Para recuperar espacio de tablas con muchas filas muertas, usa `VACUUM` (no `VACUUM FULL` en horario de producción, porque bloquea la tabla):

   ```sql
   VACUUM (VERBOSE, ANALYZE) nombre_tabla;
   ```

4. Si el espacio no alcanza, amplía el disco o sube de plan en Render. Hazlo solo con la aprobación del responsable del servicio.

### 3.D La instancia de PostgreSQL no responde o está caída

1. Revisa el estado y los eventos en el dashboard de Render.
2. Si el dashboard ofrece **reinicio** de la base de datos y tu plan lo permite, úsalo con aprobación del responsable. Espera a que el estado vuelva a *Available* antes de continuar.
3. Si no se recupera en 10 minutos o no ofrece reinicio, abre ticket con soporte de Render. Incluye el nombre de la instancia, la hora del incidente, los errores de los logs y el impacto.
4. Si el problema se prolonga, pasa a la restauración desde backup (3.G).

### 3.E Migración o cambio de código que causó el incidente

1. Si hay una migración bloqueante, cancela su sesión (paso 3.B) y evita relanzarla en horario pico.
2. Revisa qué migración quedó a medias:

   ```bash
   python manage.py showmigrations NOMBRE_APP
   python manage.py sqlmigrate NOMBRE_APP NUMERO_MIGRACION   # ver el SQL que ejecuta
   ```

3. Haz rollback del código al commit anterior estable desde el dashboard (*Rollback* o *Manual Deploy* del commit previo).
4. Si la migración ya se aplicó y debe revertirse, hazlo solo tras revisar la migración inversa con el equipo:

   ```bash
   python manage.py migrate NOMBRE_APP NUMERO_MIGRACION_ANTERIOR
   ```

   Nunca ejecutes migraciones inversas en producción sin el respaldo de 3.0.

### 3.F Credenciales o `DATABASE_URL` incorrectas

1. Verifica en el dashboard de Render que la variable del servicio web coincida con la *Internal Database URL* (para la app) o la *External* (para tu máquina local).
2. Si la credencial se rotó, actualízala en el servicio web y realiza un redeploy.
3. No pegues credenciales en chats, tickets ni logs. Si se filtraron, rótalas de inmediato.

### 3.G Restauración desde backup (último recurso)

Solo si la instancia está dañada y no se recupera. Requiere aprobación del responsable.

1. En el dashboard de PostgreSQL, usa la opción de restauración a partir de backup o point-in-time, según tu plan. Render crea una nueva instancia; no sobrescribe la anterior.
2. Si tienes un `.dump` local (paso 3.0), restáuralo en la nueva instancia:

   ```bash
   pg_restore --no-owner --no-privileges -d "$NUEVA_DATABASE_URL" backup_fitmanage_AAAAMMDD_HHMM.dump
   ```

3. Verifica conteos de tablas críticas antes de apuntar la app:

   ```sql
   SELECT count(*) FROM nombre_tabla_critica;
   ```

4. Actualiza `DATABASE_URL` en el servicio web y haz redeploy.
5. Documenta la pérdida de datos entre el último backup y el incidente.

---

## 4. Verificación tras la recuperación

Confirma los cuatro puntos antes de dar el incidente por cerrado:

```bash
# 1. Salud de la API (endpoint de health, ver abajo)
curl -sS -o /dev/null -w "%{http_code} en %{time_total}s\n" https://NOMBRE_SERVICIO.onrender.com/api/health/

# 2. Conexión desde la app (Shell de Render)
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('CONEXION OK')"
```

```sql
-- 3. Conexiones dentro de lo normal
SELECT count(*) FROM pg_stat_activity WHERE datname = current_database();

-- 4. Sin bloqueos ni transacciones atascadas
SELECT count(*) FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0;
```

Revisa también que las métricas de CPU, memoria y disco vuelvan a su rango normal y que no haya errores 5xx en los logs durante 15 minutos.

**Endpoint de health sugerido** (si todavía no existe):

```python
# health/views.py
from django.db import connection
from django.http import JsonResponse

def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"db": "ok"})
    except Exception:
        return JsonResponse({"db": "error"}, status=503)
```

Regístrala en `urls.py` (por ejemplo, `path("api/health/", health)`) y configúrala como *Health Check Path* en Render. Así Render y tu alerta detectan la caída antes que los usuarios.

---

## 5. Comunicación

- **Inicio:** "Incidente en FitManage: la API no puede conectarse a la base de datos. Equipo investigando. Hora de inicio: HH:MM."
- **Actualización cada 15-30 min:** qué se sabe, qué se hizo, qué sigue.
- **Cierre:** hora de resolución, causa preliminar, impacto y próximos pasos.

---

## 6. Post-incidente (en las 48 h siguientes)

Documenta con este formato:

1. **Resumen:** qué pasó, cuándo, cuánto duró.
2. **Impacto:** usuarios afectados, operaciones fallidas, pérdida de datos (si la hubo).
3. **Causa raíz:** usa la pregunta de los "5 porqués".
4. **Qué funcionó y qué no.**
5. **Acciones correctivas**, con responsable y fecha. Por ejemplo:
   - Ajustar `CONN_MAX_AGE`, `CONN_HEALTH_CHECKS` y los timeouts (sección 3.A).
   - Corregir la consulta o la transacción que se quedaba abierta (sección 3.B).
   - Ejecutar migraciones pesadas fuera de horario pico, con `CREATE INDEX CONCURRENTLY` cuando aplique.
   - Configurar alertas en Render para conexiones, CPU, memoria y disco, con umbrales antes del límite.
   - Probar la restauración desde backup al menos una vez, en una instancia de prueba.

---

## Apéndice: consultas útiles

```sql
-- Versión y parámetros clave
SELECT version();
SHOW max_connections;
SHOW statement_timeout;
SHOW idle_in_transaction_session_timeout;

-- Conexiones por aplicación y cliente
SELECT application_name, client_addr, count(*)
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY application_name, client_addr
ORDER BY count(*) DESC;

-- Tiempo medio de espera de consultas activas
SELECT pid, wait_event_type, wait_event, now() - query_start AS duracion
FROM pg_stat_activity
WHERE state = 'active' AND datname = current_database()
ORDER BY duracion DESC;
```

Si la app usa `pg_stat_statements`, las consultas más costosas aparecen con:

```sql
SELECT calls, round(total_exec_time::numeric, 1) AS total_ms,
       round(mean_exec_time::numeric, 1) AS media_ms, left(query, 120) AS consulta
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```
