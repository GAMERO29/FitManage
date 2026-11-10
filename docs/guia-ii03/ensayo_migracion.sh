#!/bin/bash
# Guía II-03 · ensayo de la migración 0003 en una copia aislada con datos ficticios (PostgreSQL 16).
# Uso: PGURL=postgresql://fitmanage@localhost:5433 bash docs/guia-ii03/ensayo_migracion.sh
set -u
BASE=fm_ensayo_0003
psql "$PGURL/postgres" -qc "DROP DATABASE IF EXISTS $BASE" -c "CREATE DATABASE $BASE"
export DATABASE_URL="$PGURL/$BASE" FITMANAGE_TELEMETRIA=0
q() { psql "$DATABASE_URL" -Atc "$1"; }
echo "1. Base en 0002 (lo que hay hoy en producción)"
python3 manage.py migrate persistencia 0002 -v0
python3 - <<'PY'
import django, os, uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings"); django.setup()
from django.db import connection
B = timezone(timedelta(hours=-5)); ahora = datetime(2026, 11, 10, 9, 0, tzinfo=B)
with connection.cursor() as c:
    u = uuid.uuid4(); c.execute("INSERT INTO usuarios (id,nombre,correo,rol,activo,clave_hash,intentos_fallidos) VALUES (%s,'Laura Demo','laura@demo.test','RECEPCIONISTA',true,'',0)", [u])
    p = uuid.uuid4(); c.execute("INSERT INTO planes (id,nombre,duracion_dias,precio,activo) VALUES (%s,'Mensual',30,75000,true)", [p])
    for i in range(40):
        s = uuid.uuid4()
        c.execute("INSERT INTO socios (id,tipo_documento,numero_documento,nombres,apellidos,telefono,autorizacion_datos) VALUES (%s,'CC',%s,'Socio','Prueba','3001234567',%s)", [s, f"10900{i:05d}", ahora])
        anulado = i % 4 == 0
        c.execute("INSERT INTO pagos (id,socio_id,plan_id,valor,duracion_dias,medio,referencia,fecha_inicio,fecha_vencimiento,registrado_por_id,registrado_en,estado,fecha_anulacion,anulado_por_id,motivo_anulacion) VALUES (%s,%s,%s,75000,30,'EFECTIVO',NULL,%s,%s,%s,%s,%s,%s,%s,%s)",
                  [uuid.uuid4(), s, p, date(2026, 11, 10), date(2026, 12, 9), u, ahora, "ANULADO" if anulado else "VIGENTE", ahora if anulado else None, u if anulado else None, "Plan equivocado" if anulado else None])
PY
echo "   pagos: $(q 'select count(*) from pagos') · vigentes: $(q "select count(*) from pagos where estado='VIGENTE'") · anulados: $(q "select count(*) from pagos where estado='ANULADO'")"
echo "2. Consulta previa: filas que romperían los CHECK nuevos"
echo "   $(q "select count(*) from pagos where estado not in ('VIGENTE','ANULADO') or (estado='VIGENTE' and (fecha_anulacion is not null or anulado_por_id is not null or motivo_anulacion is not null)) or (estado='ANULADO' and (fecha_anulacion is null or anulado_por_id is null or coalesce(motivo_anulacion,'')=''))")"
echo "3. migrate a 0003"
time python3 manage.py migrate persistencia 0003 -v0 && echo "   OK"
echo "   pagos después: $(q 'select count(*) from pagos') · tabla auditoria: $(q "select to_regclass('auditoria') is not null") · disparador: $(q "select count(*) from pg_trigger where tgname='auditoria_sin_cambios'")"
echo "4. Vuelta atrás a 0002 (el código anterior no conoce la tabla nueva)"
python3 manage.py migrate persistencia 0002 -v0 && echo "   OK · pagos: $(q 'select count(*) from pagos') · auditoria existe: $(q "select to_regclass('auditoria') is not null")"
echo "5. Caso negativo: una fila incoherente hace fallar la migración"
q "update pagos set motivo_anulacion=NULL where id=(select id from pagos where estado='ANULADO' limit 1)" >/dev/null
python3 manage.py migrate persistencia 0003 -v0 2>&1 | grep -E "IntegrityError|CheckViolation|violated" | head -1
echo "   estado de la migración: $(q "select coalesce(max(name),'-') from django_migrations where app='persistencia'")"
psql "$PGURL/postgres" -qc "DROP DATABASE $BASE"
