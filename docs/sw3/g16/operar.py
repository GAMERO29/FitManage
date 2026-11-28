"""Software III · Guía 16: operaciones de la prueba de restauración (datos ficticios).

Uso:  python3 docs/sw3/g16/operar.py URL antes|despues|verificar
  antes      Ana Prueba Demo paga un Mensual (queda ACTIVA). Se ejecuta antes del respaldo.
  despues    Se registra a Bruno Prueba Demo con su pago, DESPUÉS del respaldo. Es el trabajo
             que se pierde si la base se cae antes del siguiente respaldo (eso es el RPO).
  verificar  Lee lo que quedó: estado de Ana, si Bruno existe y si se puede iniciar sesión.
Nunca contra producción: deja pagos y eventos de auditoría que no se pueden borrar.
"""

import json
import sys
import urllib.error
import urllib.request
import uuid

URL = sys.argv[1].rstrip("/") + "/api/v1"
CLAVE = "clave-de-demo-local"


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


def token(correo):
    s, r = api("/auth/token", "POST", cuerpo={"correo": correo, "contrasena": CLAVE})
    return s, (r or {}).get("tokenAcceso")


def pagar(laura, doc, referencia):
    mensual = next(p["id"] for p in api("/planes", token=laura)[1] if p["nombre"] == "Mensual")
    cuerpo = {
        "tipoDocumento": "CC",
        "numeroDocumento": doc,
        "planId": mensual,
        "medio": "NEQUI",
        "referencia": referencia,
    }
    return api("/pagos", "POST", laura, cuerpo)


accion = sys.argv[2]
_, laura = token("laura@demo.local")
if accion == "antes":
    s, p = pagar(laura, "1090000011", "M200001")
    print(f"Pago de Ana antes del respaldo: HTTP {s}, vence {p.get('vence')}")
elif accion == "despues":
    s, _ = api(
        "/socios",
        "POST",
        laura,
        {
            "tipoDocumento": "CC",
            "numeroDocumento": "1090000022",
            "nombres": "Bruno",
            "apellidos": "Prueba Demo",
            "telefono": "3001234568",
            "autorizaTratamientoDatos": True,
        },
    )
    s2, p = pagar(laura, "1090000022", "M200002")
    print(f"Después del respaldo: socio Bruno HTTP {s}, su pago HTTP {s2}, vence {p.get('vence')}")
elif accion == "verificar":
    s, e = api("/estados/CC/1090000011", token=laura)
    print(f"Ana: HTTP {s}, estado={e.get('estado')}, vence={e.get('venceEl')}")
    s, _ = api("/estados/CC/1090000022", token=laura)
    print(
        f"Bruno: HTTP {s} ({'no existe: se registró después del respaldo' if s == 404 else 'existe'})"
    )
    s, _ = token("admin@demo.local")
    print(f"Inicio de sesión del administrador: HTTP {s}")
else:
    sys.exit(f"acción desconocida: {accion}")
