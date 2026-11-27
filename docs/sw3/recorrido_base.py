"""Software III · recorrido de línea base del MVP contra un servidor (local por defecto).

Datos ficticios: Ana Prueba Demo, CC 1090000011. Uso:
    docs/sw3/laboratorio.sh iniciar && python3 docs/sw3/recorrido_base.py [url]
Termina con código 1 si algún paso no da lo esperado. No se usa contra producción: deja pagos y
eventos de auditoría que no se pueden borrar.
"""

import json
import sys
import urllib.error
import urllib.request
import uuid

URL = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765").rstrip("/") + "/api/v1"
CLAVE = "clave-de-demo-local"
DOC = "1090000011"
fallas = []


def api(ruta, metodo="GET", token=None, cuerpo=None):
    cab = {"Content-Type": "application/json", "Idempotency-Key": str(uuid.uuid4())}
    if token:
        cab["Authorization"] = f"Bearer {token}"
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(URL + ruta, method=metodo, headers=cab, data=datos)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def paso(n, nombre, estado, esperado, detalle=""):
    ok = estado == esperado
    if not ok:
        fallas.append(n)
    print(
        f"R{n:02d} {'PASA ' if ok else 'FALLA'} {nombre}: HTTP {estado} (esperado {esperado}) {detalle}"
    )


def token(correo):
    return api("/auth/token", "POST", cuerpo={"correo": correo, "contrasena": CLAVE})[1][
        "tokenAcceso"
    ]


s, salud = api("/salud")
paso(1, "salud y versión", s, 200, f"version={salud['version']}")
admin = token("admin@demo.local")
s, _ = api(
    "/personal",
    "POST",
    admin,
    {
        "nombre": "Laura Demo",
        "correo": "laura@demo.local",
        "rol": "RECEPCIONISTA",
        "contrasena": CLAVE,
    },
)
paso(2, "el administrador crea a la recepcionista", s, 201)
laura = token("laura@demo.local")
s, _ = api(f"/estados/CC/{DOC}", token=laura)
paso(3, "consulta de un documento sin registrar", s, 404)
s, _ = api(
    "/socios",
    "POST",
    laura,
    {
        "tipoDocumento": "CC",
        "numeroDocumento": DOC,
        "nombres": "Ana",
        "apellidos": "Prueba Demo",
        "telefono": "3001234567",
        "autorizaTratamientoDatos": True,
    },
)
paso(4, "registrar socia (RF-01)", s, 201)
s, e = api(f"/estados/CC/{DOC}", token=laura)
paso(5, "consulta sin pagos (RF-04)", s, 200, f"estado={e['estado']}")
mensual = next(p["id"] for p in api("/planes", token=laura)[1] if p["nombre"] == "Mensual")
s, v = api(
    f"/pagos/vista-previa?tipoDocumento=CC&numeroDocumento={DOC}&planId={mensual}", token=laura
)
paso(6, "vista previa del periodo (RN-03)", s, 200, f"{v.get('inicia')} → {v.get('vence')}")
s, pago = api(
    "/pagos",
    "POST",
    laura,
    {
        "tipoDocumento": "CC",
        "numeroDocumento": DOC,
        "planId": mensual,
        "medio": "NEQUI",
        "referencia": "M123456",
    },
)
paso(7, "registrar pago Mensual por Nequi (RF-03)", s, 201, f"vence {pago.get('vence')}")
s, _ = api(
    "/pagos",
    "POST",
    laura,
    {
        "tipoDocumento": "CC",
        "numeroDocumento": DOC,
        "planId": mensual,
        "medio": "NEQUI",
        "referencia": "M123456",
    },
)
paso(8, "mismo comprobante otra vez (RN-06)", s, 409)
s, e = api(f"/estados/CC/{DOC}", token=laura)
paso(9, "consulta después del pago", s, 200, f"estado={e['estado']} vence={e.get('venceEl')}")
s, _ = api(
    f"/pagos/{pago['id']}", "PATCH", laura, {"estado": "ANULADO", "motivo": "Prueba del recorrido"}
)
paso(10, "anular el último pago con motivo (RF-10)", s, 200)
s, e = api(f"/estados/CC/{DOC}", token=laura)
paso(11, "consulta después de anular", s, 200, f"estado={e['estado']}")
hoy = salud["hora"][:10]
s, a = api(f"/auditoria?desde={hoy}&hasta={hoy}", token=admin)
eventos = [x["tipo"] for x in a.get("eventos", [])] if s == 200 else []
paso(12, "auditoría del administrador (ADR N.° 19)", s, 200, f"eventos={eventos}")

print(f"Resumen: {12 - len(fallas)} de 12 pasos dan lo esperado.")
sys.exit(1 if fallas else 0)
