"""Software III · Guía 06: DELETE /socios/{tipo}/{numero} por los tres caminos, en el laboratorio.

1. Éxito: socia ficticia sin pagos → 204 y la fila ya no está.
2. Rechazo por regla: socia con un pago → 409 SOCIO_CON_PAGOS y la fila sigue.
3. Dependencia no disponible: PostgreSQL detenido → 503 SERVICIO_NO_DISPONIBLE en problem+json;
   al volver la base, la fila sigue.
El estado de los datos se mira con psql, no con la API. Uso, con el laboratorio iniciado:
    python3 docs/sw3/g06/tres_caminos.py
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import uuid

URL = "http://127.0.0.1:8765/api/v1"
BASE = os.environ.get("BASE_SQL", "postgresql://fitmanage@localhost:5433/fm_sw3")
PG = "/usr/lib/postgresql/16/bin/pg_ctl -D /tmp/pgdata -l /tmp/pg.log -o '-p 5433 -k /tmp' -m fast"
CLAVE = "clave-de-demo-local"
fallas = 0


def api(ruta, metodo="GET", token=None, cuerpo=None):
    cab = {"Content-Type": "application/json", "Idempotency-Key": str(uuid.uuid4())}
    if token:
        cab["Authorization"] = f"Bearer {token}"
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(URL + ruta, method=metodo, headers=cab, data=datos)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.headers.get("Content-Type"), json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type"), json.loads(e.read() or b"null")


def filas(documento):
    # psql interpola :'doc' como literal citado; el documento no se concatena al SQL.
    consulta = "SELECT count(*) FROM socios WHERE numero_documento = :'doc';"
    salida = subprocess.run(
        ["psql", BASE, "-tA", "-v", f"doc={documento}"],
        input=consulta,
        capture_output=True,
        text=True,
    )
    return salida.stdout.strip()


def pg(accion):
    subprocess.run(["su", "pgrun", "-s", "/bin/bash", "-c", f"{PG} {accion}"], capture_output=True)


def revisar(nombre, ok, detalle):
    global fallas
    fallas += 0 if ok else 1
    print(f"{'PASA ' if ok else 'FALLA'} {nombre}: {detalle}")


def token(correo):
    return api("/auth/token", "POST", cuerpo={"correo": correo, "contrasena": CLAVE})[2][
        "tokenAcceso"
    ]


admin = token("admin@demo.local")
socia = {
    "tipoDocumento": "CC",
    "nombres": "Valentina",
    "apellidos": "Prueba Demo",
    "telefono": "3001234567",
    "autorizaTratamientoDatos": True,
}
api("/socios", "POST", admin, socia | {"numeroDocumento": "1090000022"})
api("/socios", "POST", admin, socia | {"numeroDocumento": "1090000033", "nombres": "Sofía"})
mensual = next(p["id"] for p in api("/planes", token=admin)[2] if p["nombre"] == "Mensual")
api(
    "/pagos",
    "POST",
    admin,
    {
        "tipoDocumento": "CC",
        "numeroDocumento": "1090000033",
        "planId": mensual,
        "medio": "EFECTIVO",
    },
)

print(f"Estado inicial: filas de 1090000022 = {filas('1090000022')}", end=" · ")
print(f"de 1090000033 = {filas('1090000033')}")
s, tipo, cuerpo = api("/socios/CC/1090000022", "DELETE", admin)
revisar(
    "1. éxito",
    s == 204 and filas("1090000022") == "0",
    f"HTTP {s}; filas después = {filas('1090000022')}",
)

s, tipo, cuerpo = api("/socios/CC/1090000033", "DELETE", admin)
revisar(
    "2. rechazo por regla",
    s == 409 and cuerpo["codigo"] == "SOCIO_CON_PAGOS" and filas("1090000033") == "1",
    f"HTTP {s} {cuerpo['codigo']}; filas después = {filas('1090000033')}",
)

pg("stop")
try:
    s, tipo, cuerpo = api("/socios/CC/1090000033", "DELETE", admin)
finally:
    pg("start")
subprocess.run(["sleep", "2"])
revisar(
    "3. base no disponible",
    s == 503
    and tipo == "application/problem+json"
    and cuerpo["codigo"] == "SERVICIO_NO_DISPONIBLE"
    and filas("1090000033") == "1",
    f"HTTP {s} {tipo} {cuerpo['codigo']}; filas al volver la base = {filas('1090000033')}",
)
sys.exit(1 if fallas else 0)
