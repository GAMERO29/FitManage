#!/bin/bash
# Guía II-04 · Fallo controlado: el proceso de la aplicación muere ENTRE el UPDATE del pago y el
# INSERT del evento de auditoría. Solo en el servidor local con datos ficticios.
#   1. Otra sesión bloquea la tabla auditoria (LOCK ... ACCESS EXCLUSIVE) durante 6 s.
#   2. Se pide la anulación: el servidor bloquea al socio, anula el pago y se queda esperando
#      para insertar el evento.
#   3. Se mata el worker de gunicorn con SIGKILL en ese momento.
#   4. Se suelta el bloqueo y se mira qué quedó guardado.
set -u
URL=http://127.0.0.1:8765/api/v1; DB=postgresql://fitmanage@localhost:5433/${BASE:-fm_ii01}; DOC=1090000011
TOKEN=$(curl -s -X POST $URL/auth/token -H 'Content-Type: application/json' -d '{"correo":"admin@demo.local","contrasena":"clave-de-demo-local"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["tokenAcceso"])')
PLAN=$(curl -s $URL/planes -H "Authorization: Bearer $TOKEN" | python3 -c 'import sys,json;print(json.load(sys.stdin)[0]["id"])')
curl -s -o /dev/null -X POST $URL/pagos -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -H "Idempotency-Key: $(python3 -c 'import uuid;print(uuid.uuid4())')" -d "{\"tipoDocumento\":\"CC\",\"numeroDocumento\":\"$DOC\",\"planId\":\"$PLAN\",\"medio\":\"EFECTIVO\"}"
PAGO=$(curl -s "$URL/socios/CC/$DOC/pagos" -H "Authorization: Bearer $TOKEN" | python3 -c 'import sys,json;print(next(p["id"] for p in json.load(sys.stdin)["pagos"] if p["estado"]=="VIGENTE"))')
q() { psql "$DB" -Atc "$1"; }
echo "Antes: pago $PAGO = $(q "select estado from pagos where id='$PAGO'") · eventos PAGO_ANULADO = $(q "select count(*) from auditoria where tipo='PAGO_ANULADO'")"
psql "$DB" -qc "BEGIN; LOCK TABLE auditoria IN ACCESS EXCLUSIVE MODE; SELECT pg_sleep(6); ROLLBACK;" &
sleep 1
curl -s -o /tmp/respuesta_fallo.txt -w "%{http_code}" -X PATCH "$URL/pagos/$PAGO" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"estado":"ANULADO","motivo":"Fallo controlado de la Guía II-04"}' > /tmp/codigo_fallo.txt &
sleep 2
echo "Mientras espera: sesiones de la app bloqueadas en el INSERT del evento = $(q "select count(*) from pg_stat_activity where wait_event_type='Lock' and query like 'INSERT INTO \"auditoria\"%'")"
WORKER=$(pgrep -f "gunicorn config.wsgi" | sort -n | tail -1)
kill -9 "$WORKER" && echo "SIGKILL al worker $WORKER"
wait
echo "Respuesta HTTP recibida por el cliente: $(cat /tmp/codigo_fallo.txt)"
sleep 2
echo "Después: pago = $(q "select estado from pagos where id='$PAGO'") · motivo = '$(q "select coalesce(motivo_anulacion,'') from pagos where id='$PAGO'")' · eventos PAGO_ANULADO = $(q "select count(*) from auditoria where tipo='PAGO_ANULADO'")"
for i in $(seq 1 20); do curl -sf $URL/salud >/dev/null && break; sleep 1; done
echo "El servicio responde de nuevo: $(curl -s $URL/salud)"
CODIGO=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$URL/pagos/$PAGO" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"estado":"ANULADO","motivo":"Reintento después del fallo"}')
echo "Reintento: HTTP $CODIGO · pago = $(q "select estado from pagos where id='$PAGO'") · eventos PAGO_ANULADO = $(q "select count(*) from auditoria where tipo='PAGO_ANULADO'")"
