#!/bin/sh
# Arranque de la imagen de producción en un PaaS sin «pre-deploy» (Render Free, ADR N.° 11).
# Aplica las migraciones y luego reemplaza este proceso por gunicorn en 0.0.0.0:$PORT.
# En docker compose no se usa: allí las migraciones son el servicio «migrar».
set -eu
echo "FitManage ${FITMANAGE_VERSION}: aplicando migraciones"
python manage.py migrate --noinput
echo "Migraciones listas; gunicorn escucha en 0.0.0.0:${PORT}"
exec gunicorn config.wsgi --bind "0.0.0.0:${PORT}" --workers 2 --timeout 60 --access-logfile -
