"""Guía II-04 · Mutaciones didácticas sobre una COPIA del repositorio (git worktree).

Cada mutación cambia una línea, corre solo las pruebas que deberían detectarla y restaura el
archivo. «Muerta» = alguna prueba falló (la detectó). «Sobrevive» = todas pasaron.
Uso: python3 mutaciones.py <carpeta-de-la-copia>   (necesita PostgreSQL en DATABASE_URL para M5 y M6)
"""
import os
import subprocess
import sys
from pathlib import Path

COPIA = Path(sys.argv[1])
PG = os.environ.get("DATABASE_URL_PG")
MUTACIONES = [
    ("M1", "Rango de 31 días: > pasa a >=", "infraestructura/api/vistas.py",
     "if hasta < desde or (hasta - desde).days > 31:", "if hasta < desde or (hasta - desde).days >= 31:",
     ["tests/integracion/api/test_api_auditoria_consulta.py"], False),
    ("M2", "El cambio de plan también registra PAGO_ANULADO", "aplicacion/pagos.py",
     "registrar_evento=not para_cambio_de_plan", "registrar_evento=True",
     ["tests/integracion/api/test_api_auditoria_pagos.py"], False),
    ("M3", "El «hoy» de la recepcionista se cuenta en UTC", "aplicacion/pagos.py",
     "pago.registrado_en.astimezone(ZONA_HORARIA).date()", "pago.registrado_en.astimezone(UTC).date()",
     ["tests/nucleo/test_anulacion.py"], False),
    ("M4", "La consulta ordena del más antiguo al más reciente", "infraestructura/consultas.py",
     'order_by("-ocurrido_en", "-id")', 'order_by("ocurrido_en", "id")',
     ["tests/integracion/api/test_api_auditoria_consulta.py"], False),
    ("M5", "Anular ya no bloquea al socio", "infraestructura/api/vistas.py",
     "        bloquear_socio_del_pago(uuid.UUID(pagoId))\n        pago = contenedor.anulacion_pago()",
     "        pago = contenedor.anulacion_pago()",
     ["tests/integracion/api/test_api_concurrencia_socio.py"], True),
    ("M6", "El disparador de PostgreSQL solo rechaza UPDATE", "infraestructura/persistencia/migrations/0003_auditoria_y_coherencia_de_anulacion.py",
     "BEFORE UPDATE OR DELETE ON auditoria", "BEFORE UPDATE ON auditoria",
     ["tests/integracion/test_auditoria_base.py"], True),
    ("M7", "El evento de pago ya no se registra", "aplicacion/pagos.py",
     "        self._pagos.guardar(pago)\n        self._auditoria.registrar(\n            EventoAuditoria(\n                TipoEvento.PAGO_REGISTRADO,",
     "        self._pagos.guardar(pago)\n        (lambda *_: None)(\n            EventoAuditoria(\n                TipoEvento.PAGO_REGISTRADO,",
     ["tests/integracion/api/test_api_auditoria_pagos.py"], False),
    ("M8", "La página pasa de 50 a 500 eventos", "infraestructura/consultas.py",
     "POR_PAGINA_AUDITORIA = 50", "POR_PAGINA_AUDITORIA = 500",
     ["tests/integracion/api/test_api_auditoria_consulta.py"], False),
    ("M9", "El evento deja de guardar el medio de pago", "dominio/auditoria.py",
     '        "medio": pago.medio.value,\n', "",
     ["tests/integracion/api/test_api_auditoria_pagos.py", "tests/integracion/api/test_api_auditoria_consulta.py"], False),
]


def correr(pruebas, en_pg):
    entorno = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
    if en_pg:
        entorno["DATABASE_URL"] = PG
    r = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-o", "addopts=", "-q",
                        "--create-db", *pruebas], cwd=COPIA, env=entorno, capture_output=True, text=True)
    return r.returncode, r.stdout.strip().splitlines()[-1]


base = correr(sorted({p for m in MUTACIONES for p in m[5] if not m[6]}), False)
print(f"Línea base (sin mutar, SQLite): {base[1]}")
for ident, que, archivo, viejo, nuevo, pruebas, en_pg in MUTACIONES:
    ruta = COPIA / archivo
    original = ruta.read_text(encoding="utf-8")
    assert original.count(viejo) == 1, f"{ident}: el texto a mutar no aparece una sola vez"
    texto = ruta.read_text(encoding="utf-8").replace(viejo, nuevo)
    if ident == "M3":
        texto = texto.replace("from uuid import UUID", "from datetime import UTC\nfrom uuid import UUID", 1)
    ruta.write_text(texto, encoding="utf-8")
    try:
        codigo, resumen = correr(pruebas, en_pg)
    finally:
        ruta.write_text(original, encoding="utf-8")
    estado = "MUERTA" if codigo != 0 else "SOBREVIVE"
    print(f"{ident} {estado:9} · {que} · {'PostgreSQL' if en_pg else 'SQLite'} · {resumen}")
