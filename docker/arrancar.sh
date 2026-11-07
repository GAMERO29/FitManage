#!/bin/sh
# Arranque de la imagen de producción en un PaaS sin «pre-deploy» (Render Free, ADR N.° 11).
# Aplica las migraciones y luego reemplaza este proceso por gunicorn en 0.0.0.0:$PORT.
# En docker compose no se usa: allí las migraciones son el servicio «migrar».
set -eu
echo "FitManage ${FITMANAGE_VERSION}: aplicando migraciones"
python manage.py migrate --noinput
# Guía 16: planes iniciales y primera cuenta de administrador, solo si no existen.
python manage.py preparar_gimnasio
echo "Migraciones listas; gunicorn escucha en 0.0.0.0:${PORT}"
# Un proceso con 4 hilos y sin access log (ADR N.° 13): ver el comentario del CMD en el Dockerfile.
exec gunicorn config.wsgi --bind "0.0.0.0:${PORT}" --workers 1 --threads 4 --timeout 60
