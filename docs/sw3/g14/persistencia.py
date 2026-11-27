"""Software III · Guía 14: atomicidad, repetición y permanencia de la anulación en el laboratorio.

Con el laboratorio iniciado (docs/sw3/laboratorio.sh iniciar):
    python3 docs/sw3/g14/persistencia.py
El estado se lee con psql, no con la API. Datos ficticios.
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

URL = "http://127.0.0.1:8765/api/v1"
BASE = os.environ.get("BASE_SQL", "postgresql://fitmanage@localhost:5433/fm_sw3")
PG = "/usr/lib/postgresql/16/bin/pg_ctl -D /tmp/pgdata -l /tmp/pg.log -o '-p 5433 -k /tmp' -m fast"
CLAVE, DOC = "clave-de-demo-local", "1090000066"
fallas = 0


def api(ruta, metodo="GET", token=None, cuerpo=None, clave=None):
    cab = {"Content-Type": "application/json", "Idempotency-Key": clave or str(uuid.uuid4())}
    if token:
        cab["Authorization"] = f"Bearer {token}"
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(URL + ruta, method=metodo, headers=cab, data=datos)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def sql(consulta, **variables):
    """psql con variables citadas (:'x'); nada del exterior se concatena al SQL."""
    args = ["psql", BASE, "-tA", "-F", " | "]
    for nombre, valor in variables.items():
        args += ["-v", f"{nombre}={valor}"]
    return subprocess.run(args, input=consulta, capture_output=True, text=True).stdout.strip()


def estado_del_pago(pago_id):
    return sql(
        "SELECT estado, coalesce(motivo_anulacion, '-') FROM pagos WHERE id = :'id';", id=pago_id
    )


def eventos(tipo, entidad):
    return sql(
        "SELECT count(*) FROM auditoria WHERE tipo = :'t' AND entidad_id = :'e';", t=tipo, e=entidad
    )


def revisar(nombre, ok, detalle):
    global fallas
    fallas += 0 if ok else 1
    print(f"{'PASA ' if ok else 'FALLA'} {nombre}: {detalle}")


def token():
    return api("/auth/token", "POST", cuerpo={"correo": "admin@demo.local", "contrasena": CLAVE})[
        1
    ]["tokenAcceso"]


admin = token()
api(
    "/socios",
    "POST",
    admin,
    {
        "tipoDocumento": "CC",
        "numeroDocumento": DOC,
        "nombres": "Elena",
        "apellidos": "Prueba Demo",
        "telefono": "3001234567",
        "autorizaTratamientoDatos": True,
    },
)
mensual = next(p["id"] for p in api("/planes", token=admin)[1] if p["nombre"] == "Mensual")
pago_de = {"tipoDocumento": "CC", "numeroDocumento": DOC, "planId": mensual, "medio": "EFECTIVO"}

# 1. Escritura repetida del registro: la misma Idempotency-Key no crea un segundo pago.
clave = str(uuid.uuid4())
s1, p1 = api("/pagos", "POST", admin, pago_de, clave)
s2, p2 = api("/pagos", "POST", admin, pago_de, clave)
filas = sql(
    "SELECT count(*) FROM pagos p JOIN socios s ON s.id = p.socio_id"
    " WHERE s.numero_documento = :'d';",
    d=DOC,
)
revisar(
    "1. repetir POST /pagos con la misma clave",
    (s1, s2) == (201, 201) and p1["id"] == p2["id"] and filas == "1",
    f"HTTP {s1} y {s2}, mismo id = {p1['id'] == p2['id']}, filas en pagos = {filas}",
)
pago = p1["id"]
inicial = eventos("PAGO_ANULADO", pago)
print(f"   estado inicial: {estado_del_pago(pago)} · eventos PAGO_ANULADO = {inicial}")

# 2. Anular y repetir la anulación: el efecto ocurre una vez, la segunda es 409 y no deja evento.
cuerpo = {"estado": "ANULADO", "motivo": "Prueba de la guía 14"}
a1, _ = api(f"/pagos/{pago}", "PATCH", admin, cuerpo)
a2, r2 = api(f"/pagos/{pago}", "PATCH", admin, cuerpo)
revisar(
    "2. repetir la anulación",
    (a1, a2) == (200, 409) and eventos("PAGO_ANULADO", pago) == "1",
    f"HTTP {a1} y luego {a2} {r2['codigo']}; estado = {estado_del_pago(pago)}; "
    f"eventos PAGO_ANULADO = {eventos('PAGO_ANULADO', pago)}",
)

# 3. Permanencia: se detienen gunicorn y PostgreSQL, se vuelven a iniciar y se lee lo confirmado.
subprocess.run(["pkill", "-f", "gunicorn config.wsgi --bind 127.0.0.1:8765"])
subprocess.run(["su", "pgrun", "-s", "/bin/bash", "-c", f"{PG} stop"], capture_output=True)
time.sleep(1)
subprocess.run(["su", "pgrun", "-s", "/bin/bash", "-c", f"{PG} start"], capture_output=True)
time.sleep(2)
entorno = os.environ | {
    "DATABASE_URL": BASE,
    "DJANGO_SECRET_KEY": "solo-laboratorio-local",
    "JWT_CLAVE": "solo-laboratorio-local-jwt",
    "FITMANAGE_TELEMETRIA": "0",
}
servidor = subprocess.Popen(
    ["gunicorn", "config.wsgi", "--bind", "127.0.0.1:8765", "--workers", "1"],
    env=entorno,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True,
)
for _ in range(40):
    try:
        urllib.request.urlopen(URL + "/salud", timeout=2)
        break
    except OSError:
        time.sleep(0.5)
historial = api(f"/socios/CC/{DOC}/pagos", token=token())[1]["pagos"]
revisar(
    "3. permanencia tras reiniciar la aplicación y la base",
    estado_del_pago(pago) == "ANULADO | Prueba de la guía 14"
    and historial[0]["estado"] == "ANULADO",
    f"psql = {estado_del_pago(pago)}; la API dice {historial[0]['estado']} con motivo "
    f"«{historial[0]['anulacion']['motivo']}»",
)

# 4. La auditoría no se vacía con TRUNCATE desde psql (ADR N.° 20).
antes = sql("SELECT count(*) FROM auditoria;")
error = subprocess.run(
    ["psql", BASE, "-tA", "-c", "TRUNCATE auditoria"], capture_output=True, text=True
).stderr.strip()
despues = sql("SELECT count(*) FROM auditoria;")
revisar(
    "4. TRUNCATE auditoria desde psql",
    "no se puede vaciar" in error and antes == despues,
    f"filas antes = {antes}, después = {despues}; psql: "
    f"{error.splitlines()[0] if error else '(sin error)'}",
)
sys.exit(1 if fallas else 0)
