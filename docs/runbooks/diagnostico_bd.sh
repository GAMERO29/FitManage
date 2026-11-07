#!/usr/bin/env bash
# Paso 2 del Runbook_base_de_datos.md: diagnóstico en un minuto, sin cambiar nada.
#   docs/runbooks/diagnostico_bd.sh produccion   # la app en Render
#   docs/runbooks/diagnostico_bd.sh compose      # docker compose en este equipo
# Solo lee: no reinicia ni borra nada. El simulacro de la Guía 14 lo corre tal cual.
set -u
entorno="${1:-produccion}"
case "$entorno" in
  produccion) url="https://fitmanage-svol.onrender.com" ;;
  compose) url="http://127.0.0.1:8000" ;;
  *) echo "uso: $0 produccion|compose" >&2; exit 2 ;;
esac

echo "== 1. ¿La app responde y ve la base? (/api/v1/salud)"
codigo=$(curl -s -o /tmp/salud.json -w '%{http_code}' --max-time 70 "$url/api/v1/salud")
echo "HTTP $codigo: $(cat /tmp/salud.json 2>/dev/null)"
case "$codigo" in
  200) echo "=> La app y la base están bien. Si hay alerta, el problema es otro: revisar el tablero." ;;
  503) echo "=> La app está viva pero NO llega a la base (SERVICIO_NO_DISPONIBLE). Seguir con el paso 3." ;;
  000) echo "=> No hubo respuesta: la app misma está caída o despertando. Ir al paso 3.D." ;;
  *) echo "=> Respuesta inesperada: revisar los logs de la app." ;;
esac

if [ "$entorno" = "compose" ]; then
  echo "== 2. Estado del contenedor de la base"
  docker compose ps -a db --format 'table {{.Service}}\t{{.State}}\t{{.Status}}'
  echo "== 3. ¿PostgreSQL acepta conexiones?"
  docker compose exec -T db pg_isready -U fitmanage 2>&1 || true
  echo "== 4. Últimas líneas de la base"
  docker compose logs --no-color --tail 15 db 2>&1 | cut -c1-200
  echo "== 5. Último error de la app (log JSON)"
  docker compose logs --no-color app 2>&1 | grep '"nivel": "ERROR"' | tail -1 \
    | sed 's/^[^{]*//' | python3 -c 'import json,sys
for l in sys.stdin:
    j = json.loads(l); print(j["momento"], j["mensaje"]); print("   ", j.get("excepcion", "").strip().splitlines()[-1][:200])' \
    || echo "(sin errores en el log)"
fi
