"""Resume el muestreo con las trazas que el workflow Observabilidad bajó de Jaeger (API v3).

Uso: python observabilidad/ci/trazas.py <peticiones_totales>   (lee trazas.json)
Escribe trace_id.txt con una traza que tenga el span consultar_estado.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path


def a_hex(valor: str) -> str:
    """jsonpb puede entregar los IDs en hexadecimal o en base64, según la versión."""
    if len(valor) in (16, 32) and all(c in "0123456789abcdef" for c in valor.lower()):
        return valor.lower()
    return base64.b64decode(valor).hex()


def atributos(span: dict) -> dict:
    return {a["key"]: next(iter(a["value"].values())) for a in span.get("attributes", [])}


def main() -> None:
    peticiones = int(float(sys.argv[1]))
    crudo = Path("trazas.json").read_bytes()
    spans = [
        s
        for rs in json.loads(crudo)["result"]["resourceSpans"]
        for ss in rs.get("scopeSpans", [])
        for s in ss.get("spans", [])
    ]
    trazas = {a_hex(s["traceId"]) for s in spans}
    print(
        f"Peticiones: {peticiones} · trazas guardadas: {len(trazas)} · "
        f"proporción: {len(trazas) / peticiones:.3f} (configurada: 0.1)"
    )
    ejemplo = next(s for s in spans if s["name"] == "consultar_estado")
    trace_id = a_hex(ejemplo["traceId"])
    Path("trace_id.txt").write_text(trace_id)
    print(f"Traza de ejemplo {trace_id}:")
    for s in spans:
        if a_hex(s["traceId"]) == trace_id:
            dur_ms = (int(s["endTimeUnixNano"]) - int(s["startTimeUnixNano"])) / 1e6
            print(f"  {s['name']}  {dur_ms:.2f} ms  {json.dumps(atributos(s), ensure_ascii=False)}")


if __name__ == "__main__":
    main()
