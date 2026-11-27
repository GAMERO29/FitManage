#!/bin/bash
# Software III · laboratorio local: una base PostgreSQL nueva y gunicorn con el commit actual.
# Uso:  docs/sw3/laboratorio.sh iniciar [base]   ·   docs/sw3/laboratorio.sh detener
# Solo para pruebas locales con datos ficticios. La clave del administrador es de demostración.
set -euo pipefail
RAIZ=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
PUERTO=${PUERTO:-8765}
SERVIDOR_PG=${SERVIDOR_PG:-postgresql://fitmanage@localhost:5433}
BASE=${2:-fm_sw3}
LOG=${LOG:-/tmp/fitmanage_sw3.log}

detener() { pkill -f "gunicorn config.wsgi --bind 127.0.0.1:${PUERTO}" 2>/dev/null || true; sleep 1; }

case "${1:-}" in
  iniciar)
    detener
    psql "$SERVIDOR_PG/postgres" -qc "DROP DATABASE IF EXISTS $BASE WITH (FORCE)" -c "CREATE DATABASE $BASE" >/dev/null
    export DATABASE_URL="$SERVIDOR_PG/$BASE" DJANGO_SECRET_KEY=solo-laboratorio-local JWT_CLAVE=solo-laboratorio-local-jwt \
      FITMANAGE_TELEMETRIA=0 FITMANAGE_VERSION=$(git -C "$RAIZ" rev-parse --short HEAD) \
      FITMANAGE_ADMIN_NOMBRE="Admin Demo" FITMANAGE_ADMIN_CORREO=admin@demo.local FITMANAGE_ADMIN_CLAVE=clave-de-demo-local \
      EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend
    cd "$RAIZ"
    python3 manage.py migrate --noinput >/dev/null
    python3 manage.py preparar_gimnasio >/dev/null
    nohup gunicorn config.wsgi --bind "127.0.0.1:${PUERTO}" --workers 1 --threads 4 --timeout 60 >"$LOG" 2>&1 &
    for _ in $(seq 1 40); do curl -sf "http://127.0.0.1:${PUERTO}/api/v1/salud" >/dev/null && break; sleep 0.5; done
    curl -s "http://127.0.0.1:${PUERTO}/api/v1/salud"; echo
    ;;
  detener) detener ;;
  *) echo "uso: $0 iniciar [base] | detener" >&2; exit 2 ;;
esac
