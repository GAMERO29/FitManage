#!/bin/bash
# Guía II-05 · Entrega controlada, incidente y recuperación en dos entornos locales separados.
#   Destino: base fm_ii05 + puerto 8770. Empieza con la versión anterior (992ddc7, esquema 0002),
#   que es lo que corría en producción antes de las guías II, y se actualiza a la candidata.
#   Restauración: base aparte fm_ii05_restaurada. Datos ficticios. Nunca toca Render.
# Uso: CANDIDATA=<carpeta del código candidato> ANTERIOR=<carpeta de 992ddc7> bash entrega_controlada.sh
set -u
PG=postgresql://fitmanage@localhost:5433; BASE=fm_ii05; URL=http://127.0.0.1:8770/api/v1; DOC=1090000011
BIN=/usr/lib/postgresql/16/bin
t() { date +%H:%M:%S; }
q() { psql "$PG/$BASE" -Atc "$1"; }
arrancar() { # $1 carpeta, $2 versión, $3 puerto
  (cd "$1" && DATABASE_URL=$PG/$BASE DJANGO_SECRET_KEY=solo-local-ii05 JWT_CLAVE=solo-local-ii05-jwt-de-32-bytes-o-mas FITMANAGE_TELEMETRIA=0 \
   FITMANAGE_VERSION=$2 exec gunicorn config.wsgi --bind 127.0.0.1:$3 --workers 1 --threads 4 >> /tmp/ii05_$3.log 2>&1 &)
  for i in $(seq 1 30); do curl -sf http://127.0.0.1:$3/api/v1/salud >/dev/null && return 0; sleep 0.5; done; return 1
}
token() { curl -s -X POST $URL/auth/token -H 'Content-Type: application/json' -d "{\"correo\":\"$1\",\"contrasena\":\"clave-de-demo-local\"}" | python3 -c 'import sys,json;print(json.load(sys.stdin)["tokenAcceso"])'; }
pagar() { # $1 token, $2 plan, $3 medio, $4 comprobante (opcional)
  cuerpo=$(python3 -c "import json,sys;d={'tipoDocumento':'CC','numeroDocumento':'$DOC','planId':'$2','medio':'$3'};r='${4:-}';d.update({'referencia':r} if r else {});print(json.dumps(d))")
  curl -s -o /dev/null -w "%{http_code}" -X POST $URL/pagos -H "Authorization: Bearer $1" -H 'Content-Type: application/json' -H "Idempotency-Key: $(python3 -c 'import uuid;print(uuid.uuid4())')" -d "$cuerpo"; }

pkill -f "gunicorn config.wsgi"; sleep 1
psql $PG/postgres -qc "DROP DATABASE IF EXISTS $BASE" -c "DROP DATABASE IF EXISTS ${BASE}_restaurada" -c "CREATE DATABASE $BASE" 2>/dev/null
echo "== 0. Línea base: el destino corre la versión anterior"
(cd "$ANTERIOR" && export DATABASE_URL=$PG/$BASE FITMANAGE_ADMIN_NOMBRE="Carlos Demo" FITMANAGE_ADMIN_CORREO=admin@demo.local FITMANAGE_ADMIN_CLAVE=clave-de-demo-local \
  && python3 manage.py migrate -v0 && python3 manage.py preparar_gimnasio >/dev/null)
arrancar "$ANTERIOR" 992ddc7 8770
echo "$(t) salud: $(curl -s $URL/salud)"
ADM=$(token admin@demo.local)
curl -s -o /dev/null -X POST $URL/personal -H "Authorization: Bearer $ADM" -H 'Content-Type: application/json' -d '{"nombre":"Laura Demo","correo":"laura@demo.local","rol":"RECEPCIONISTA","contrasena":"clave-de-demo-local"}'
curl -s -o /dev/null -X POST $URL/socios -H "Authorization: Bearer $ADM" -H 'Content-Type: application/json' -d "{\"tipoDocumento\":\"CC\",\"numeroDocumento\":\"$DOC\",\"nombres\":\"Ana\",\"apellidos\":\"Prueba Demo\",\"telefono\":\"3001234567\",\"autorizaTratamientoDatos\":true}"
PLAN=$(curl -s $URL/planes -H "Authorization: Bearer $ADM" | python3 -c 'import sys,json;print(next(p["id"] for p in json.load(sys.stdin) if p["nombre"]=="Mensual"))')
echo "$(t) pago con la versión anterior: HTTP $(pagar $(token laura@demo.local) $PLAN NEQUI M123456) · migración: $(q "select max(name) from django_migrations where app='persistencia'")"

echo "== 1. Respaldo antes de cambiar, y prueba de que sirve"
$BIN/pg_dump -Fc -d $PG/$BASE -f /tmp/ii05_respaldo_previo.dump
psql $PG/postgres -qc "CREATE DATABASE ${BASE}_verif" && $BIN/pg_restore -d $PG/${BASE}_verif /tmp/ii05_respaldo_previo.dump
echo "$(t) respaldo: $(du -h /tmp/ii05_respaldo_previo.dump | cut -f1) · pagos en la copia de verificación: $(psql $PG/${BASE}_verif -Atc 'select count(*) from pagos')"
psql $PG/postgres -qc "DROP DATABASE ${BASE}_verif"

echo "== 2. Ventana de cambio: parada controlada, migración, versión nueva"
INICIO=$(date +%s.%N); echo "$(t) se detiene la versión anterior"; pkill -f "127.0.0.1:8770"; sleep 1
(cd "$CANDIDATA" && DATABASE_URL=$PG/$BASE python3 manage.py migrate -v0) && echo "$(t) migración aplicada: $(q "select max(name) from django_migrations where app='persistencia'")"
arrancar "$CANDIDATA" 359aaeb 8770 && FIN=$(date +%s.%N)
echo "$(t) versión nueva en línea: $(curl -s $URL/salud) · servicio detenido $(python3 -c "print(round($FIN-$INICIO,1))") s"

echo "== 3. Verificación funcional con datos ficticios"
ADM=$(token admin@demo.local); LAU=$(token laura@demo.local)
echo "$(t) pago nuevo: HTTP $(pagar $LAU $PLAN EFECTIVO)"
ULT=$(curl -s "$URL/socios/CC/$DOC/pagos" -H "Authorization: Bearer $ADM" | python3 -c 'import sys,json;print(json.load(sys.stdin)["pagos"][0]["id"])')
echo "$(t) anulación del último: HTTP $(curl -s -o /dev/null -w "%{http_code}" -X PATCH $URL/pagos/$ULT -H "Authorization: Bearer $ADM" -H 'Content-Type: application/json' -d '{"estado":"ANULADO","motivo":"Verificación posterior al despliegue"}')"
HOY=$(TZ=America/Bogota date +%F)
echo "$(t) auditoría de hoy: $(curl -s "$URL/auditoria?desde=$HOY&hasta=$HOY" -H "Authorization: Bearer $ADM" | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["total"],"eventos:",", ".join(e["tipo"] for e in d["eventos"]))')"
echo "$(t) la recepcionista consulta la auditoría: HTTP $(curl -s -o /dev/null -w "%{http_code}" "$URL/auditoria?desde=$HOY&hasta=$HOY" -H "Authorization: Bearer $LAU")"
echo "$(t) estado de la socia: $(curl -s $URL/estados/CC/$DOC -H "Authorization: Bearer $LAU" | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["estado"], "hasta", d.get("venceEl"))')"
echo "$(t) pagos en la base: $(q 'select count(*) from pagos') · eventos: $(q 'select count(*) from auditoria')"

echo "== 4. Incidente controlado: la base de datos se cae"
su pgrun -s /bin/bash -c "$BIN/pg_ctl -D /tmp/pgdata -m fast stop" >/dev/null; CAIDA=$(date +%s.%N); echo "$(t) PostgreSQL detenido"
for i in $(seq 1 20); do c=$(curl -s -o /dev/null -w "%{http_code}" $URL/salud); [ "$c" = "503" ] && break; sleep 0.5; done
DETECTA=$(date +%s.%N); echo "$(t) /salud responde $c (detectado en $(python3 -c "print(round($DETECTA-$CAIDA,1))") s) · una consulta de estado responde HTTP $(curl -s -o /dev/null -w "%{http_code}" $URL/estados/CC/$DOC -H "Authorization: Bearer $LAU")"
sleep 3; echo "$(t) diagnóstico: el log de gunicorn muestra $(grep -c 'OperationalError\|connection' /tmp/ii05_8770.log) líneas de error de conexión"
ACCION=$(date +%s.%N); echo "$(t) acción: arrancar PostgreSQL de nuevo"
su pgrun -s /bin/bash -c "$BIN/pg_ctl -D /tmp/pgdata -l /tmp/pg.log -o '-p 5433 -k /tmp' start" >/dev/null
for i in $(seq 1 40); do curl -sf $URL/salud >/dev/null && break; sleep 0.5; done
VUELVE=$(date +%s.%N); echo "$(t) servicio recuperado: $(curl -s $URL/salud | python3 -c 'import sys,json;print(json.load(sys.stdin)["estado"])') · de la acción al servicio: $(python3 -c "print(round($VUELVE-$ACCION,1))") s · caída total (incluye 3 s de diagnóstico a propósito): $(python3 -c "print(round($VUELVE-$CAIDA,1))") s"
echo "$(t) operación después de recuperar: pago HTTP $(pagar $LAU $PLAN EFECTIVO) · pagos $(q 'select count(*) from pagos') · eventos $(q 'select count(*) from auditoria')"

echo "== 5. Restauración del respaldo previo en un destino separado"
psql $PG/postgres -qc "CREATE DATABASE ${BASE}_restaurada" && $BIN/pg_restore -d $PG/${BASE}_restaurada /tmp/ii05_respaldo_previo.dump
R() { psql $PG/${BASE}_restaurada -Atc "$1"; }
echo "$(t) restaurada: pagos $(R 'select count(*) from pagos') (vivos $(q 'select count(*) from pagos')) · migración $(R "select max(name) from django_migrations where app='persistencia'") · tabla auditoria: $(R "select to_regclass('auditoria') is not null")"
echo "$(t) se perderían si se restaurara: $(($(q 'select count(*) from pagos') - $(R 'select count(*) from pagos'))) pagos y $(q 'select count(*) from auditoria') eventos (todo lo posterior al respaldo)"

echo "== 6. ¿Se puede volver a la versión anterior con el esquema nuevo?"
pkill -f "127.0.0.1:8770"; sleep 1; arrancar "$ANTERIOR" 992ddc7 8770
echo "$(t) versión anterior sobre el esquema 0003: $(curl -s $URL/salud | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["estado"], d["version"])')"
ANTES=$(q 'select count(*) from auditoria'); echo "$(t) pago con la versión anterior: HTTP $(pagar $(token laura@demo.local) $PLAN EFECTIVO) · eventos antes $ANTES, después $(q 'select count(*) from auditoria')"
pkill -f "127.0.0.1:8770"
