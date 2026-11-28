#!/bin/bash
# Software III · Guía 16: puesta en marcha reproducible y recuperación del MVP en el laboratorio.
#
#   docs/sw3/g16/despliegue_reproducible.sh [commit]      (por defecto, el commit actual)
#
# Despliega UNA versión fija (un commit, el mismo que identifica la imagen sha-<commit> de GHCR)
# en un directorio aparte, con una base nueva y datos ficticios; corre salud y el recorrido
# nominal; saca un respaldo con pg_dump; registra trabajo después del respaldo; borra la base para
# simular su pérdida; restaura el respaldo y verifica salud, persistencia y lo que se perdió.
# Mide el tiempo de restablecimiento (RTO observado) y la ventana perdida (RPO observado).
# Solo laboratorio local: nunca contra producción.
set -euo pipefail
RAIZ=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
VERSION=$(git -C "$RAIZ" rev-parse "${1:-HEAD}")
CORTA=${VERSION:0:7}
PUERTO=${PUERTO:-8766}
SERVIDOR_PG=${SERVIDOR_PG:-postgresql://fitmanage@localhost:5433}
BASE=fm_g16
DIR=/tmp/fitmanage-$CORTA
RESPALDO=/tmp/fm_g16-respaldo.dump
URL=http://127.0.0.1:$PUERTO
ahora() { date +%s.%N; }
seg() { python3 -c "print(f'{$2 - $1:.1f}')"; }
detener() { pkill -f "gunicorn config.wsgi --bind 127.0.0.1:${PUERTO}" 2>/dev/null || true; sleep 1; }
esperar_salud() { for _ in $(seq 1 60); do curl -sf "$URL/api/v1/salud" >/dev/null && return 0; sleep 0.5; done; return 1; }

# 1. Variables declaradas (ver variables.env.ejemplo). Las claves se generan en cada corrida.
export DATABASE_URL="$SERVIDOR_PG/$BASE" DJANGO_SECRET_KEY=$(openssl rand -hex 32) JWT_CLAVE=$(openssl rand -hex 32) \
  FITMANAGE_TELEMETRIA=0 FITMANAGE_VERSION=$CORTA \
  FITMANAGE_ADMIN_NOMBRE="Admin Demo" FITMANAGE_ADMIN_CORREO=admin@demo.local FITMANAGE_ADMIN_CLAVE=clave-de-demo-local \
  EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend

# Mismo comando que docker/arrancar.sh en Render: 1 proceso, 4 hilos.
arrancar() { (cd "$DIR" && nohup gunicorn config.wsgi --bind "127.0.0.1:${PUERTO}" --workers 1 --threads 4 --timeout 60 >/tmp/fm_g16.log 2>&1 &); }

echo "# $(date -Iseconds) · versión $VERSION · $(python3 --version) · $(psql --version)"
echo "## 1. Artefacto fijo"
detener
git -C "$RAIZ" worktree remove --force "$DIR" 2>/dev/null || true
git -C "$RAIZ" worktree add --detach "$DIR" "$VERSION" >/dev/null 2>&1
echo "Directorio $DIR en el commit $(git -C "$DIR" rev-parse --short HEAD), sin cambios locales: $(git -C "$DIR" status --porcelain | wc -l) archivos modificados"

echo "## 2. Puesta en marcha en limpio"
t0=$(ahora)
psql "$SERVIDOR_PG/postgres" -qc "DROP DATABASE IF EXISTS $BASE WITH (FORCE)" -c "CREATE DATABASE $BASE" >/dev/null
(cd "$DIR" && python3 manage.py migrate --noinput | tail -1 && python3 manage.py preparar_gimnasio | tail -1)
arrancar; esperar_salud
echo "Salud: $(curl -s "$URL/api/v1/salud") · puesta en marcha en $(seg "$t0" "$(ahora)") s"

echo "## 3. Operación nominal (recorrido de línea base)"
python3 "$RAIZ/docs/sw3/recorrido_base.py" "$URL" | tail -13
python3 "$RAIZ/docs/sw3/g16/operar.py" "$URL" antes

echo "## 4. Respaldo"
contar() { psql "$DATABASE_URL" -Atc "SELECT 'socios=' || (SELECT count(*) FROM socios) || ' pagos=' || (SELECT count(*) FROM pagos) || ' auditoria=' || (SELECT count(*) FROM auditoria)"; }
pg_dump -Fc "$DATABASE_URL" -f "$RESPALDO"
t_respaldo=$(ahora)
echo "Respaldo $(basename $RESPALDO): $(du -h "$RESPALDO" | cut -f1), $(date -Iseconds) · $(contar)"
sleep 5
python3 "$RAIZ/docs/sw3/g16/operar.py" "$URL" despues
echo "Estado antes de la falla: $(contar)"

echo "## 5. Falla simulada: se pierde la base"
t_falla=$(ahora)
psql "$SERVIDOR_PG/postgres" -qc "DROP DATABASE $BASE WITH (FORCE)"
echo "Salud con la base perdida: $(curl -s -o /dev/null -w 'HTTP %{http_code}' "$URL/api/v1/salud")"

echo "## 6. Restauración"
detener
psql "$SERVIDOR_PG/postgres" -qc "CREATE DATABASE $BASE"
pg_restore --no-owner -d "$DATABASE_URL" "$RESPALDO"
(cd "$DIR" && python3 manage.py migrate --noinput | tail -1)
arrancar; esperar_salud
t_listo=$(ahora)
echo "Salud: $(curl -s "$URL/api/v1/salud")"

echo "## 7. Verificación del estado restaurado"
echo "Conteos: $(contar)"
python3 "$RAIZ/docs/sw3/g16/operar.py" "$URL" verificar
echo "TRUNCATE de la auditoría tras restaurar: $(psql "$DATABASE_URL" -Atc 'TRUNCATE auditoria' 2>&1 | head -1)"
echo "RTO observado (de la pérdida a la salud OK): $(seg "$t_falla" "$t_listo") s"
echo "RPO observado (trabajo hecho después del último respaldo): $(seg "$t_respaldo" "$t_falla") s y lo que se registró en ellos"
detener
git -C "$RAIZ" worktree remove --force "$DIR"
