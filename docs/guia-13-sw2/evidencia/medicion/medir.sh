#!/bin/bash
# Mide el costo de la telemetría (Guía 13). Requiere la base fitmanage_carga sembrada y el colector falso:
#   python docs/guia-13-sw2/evidencia/medicion/colector_falso.py &
#   ./medir.sh sin-telemetria 0 0.1 ; ./medir.sh con-10 1 0.1 ; ./medir.sh con-100 1 1.0
# DATABASE_URL apunta a la base local de carga (pruebas_carga/sembrar.py).
set -u
cd "$(git rev-parse --show-toplevel)"; SALIDA=${SALIDA:-/tmp/medicion}; mkdir -p "$SALIDA"
export DATABASE_URL=${DATABASE_URL:?Defina DATABASE_URL de la base _carga} JWT_CLAVE=$(openssl rand -hex 32) DJANGO_SECRET_KEY=fija-para-medir-$(date +%s)
export FITMANAGE_TELEMETRIA=$2 OTEL_TRACES_SAMPLER_ARG=$3 OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
gunicorn config.wsgi --bind 127.0.0.1:8000 --workers 1 --threads 4 > $SALIDA/$1-app.log 2>&1 &
G=$!
sleep 4
k6 run --quiet --stage 15s:10 --stage 90s:10 --stage 5s:0 --summary-export $SALIDA/$1.json pruebas_carga/consulta_estado.js > $SALIDA/$1-k6.txt 2>&1
W=$(pgrep -P $G | head -1); CPU=$(awk '{print ($14+$15)/100}' /proc/$W/stat); echo "cpu_s=$CPU"; kill $G; sleep 2
python3 -c "
import json,sys; d=json.load(open('$SALIDA/$1.json'))['metrics']
m=d['http_req_duration{endpoint:consultarEstado}'] if 'http_req_duration{endpoint:consultarEstado}' in d else d['http_req_duration']
print('$1', 'p50=%.2f p95=%.2f ms' % (m['med'], m['p(95)']), 'reqs=%d' % d['http_reqs']['count'], 'fallas=%.3f' % d['http_req_failed']['value'])"
ls -l $SALIDA/$1-app.log | awk '{print "bytes de log:",$5}'
