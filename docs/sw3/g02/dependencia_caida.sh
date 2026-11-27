#!/bin/bash
# Software III · Guía 02: recorrido nominal y con la base detenida, en el laboratorio local.
# Requiere docs/sw3/laboratorio.sh iniciado y un PostgreSQL local que se pueda detener con pg_ctl.
# pg() detiene o arranca ese PostgreSQL; cámbiela si su laboratorio usa otro.
set -uo pipefail
URL=http://127.0.0.1:${PUERTO:-8765}/api/v1
pg() { su pgrun -s /bin/bash -c "/usr/lib/postgresql/16/bin/pg_ctl -D /tmp/pgdata -l /tmp/pg.log -o '-p 5433 -k /tmp' -m fast $1" >/dev/null; }
LOG=${LOG:-/tmp/fitmanage_sw3.log}
t() { date +%H:%M:%S.%3N; }
tok=$(curl -s -X POST $URL/auth/token -H 'Content-Type: application/json' \
  -d '{"correo":"laura@demo.local","contrasena":"clave-de-demo-local"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["tokenAcceso"])')
consulta() { curl -s -o /tmp/cuerpo.json -w '%{http_code} %{time_total}s' -H "Authorization: Bearer $tok" $URL/estados/CC/1090000011; }
echo "== Condición 1: nominal"
echo "$(t) /salud: $(curl -s -o /dev/null -w '%{http_code}' $URL/salud) · consulta de estado: $(consulta) · $(python3 -c 'import json;d=json.load(open("/tmp/cuerpo.json"));print(d.get("estado"))')"
echo "== Condición 2: la base de datos no está disponible"
lineas_antes=$(wc -l < "$LOG")
pg stop && echo "$(t) PostgreSQL detenido"
echo "$(t) /salud: $(curl -s -o /dev/null -w '%{http_code}' $URL/salud) · consulta de estado: $(consulta) · tipo de cuerpo: $(head -c 15 /tmp/cuerpo.json | tr -d "\n")…"
echo "$(t) registro del servidor (solo nivel y mensaje, sin datos de la consulta):"
tail -n +$((lineas_antes + 1)) "$LOG" | python3 -c '
import sys, json
for l in sys.stdin:
    try: d = json.loads(l)
    except ValueError: continue
    if d.get("nivel") in ("ERROR", "WARNING"):
        ultima = (d.get("excepcion") or d.get("exc_info") or "").strip().splitlines()[-1:] or [""]
        print("   ", d.get("nivel"), "·", d.get("logger"), "·", d.get("mensaje", "")[:60], "·", ultima[0][:110])' | sort | uniq -c | head -5
pg start && sleep 2 && echo "$(t) PostgreSQL arrancado de nuevo"
echo "== Condición 3: recuperación sin reiniciar la aplicación"
echo "$(t) /salud: $(curl -s -o /dev/null -w '%{http_code}' $URL/salud) · consulta de estado: $(consulta)"
