"""Guía II-02 · métricas de flujo reproducibles con la historia real de PR del repositorio.

Datos: `prs_2026-11-09.tsv` y `prs_tamano_2026-11-09.tsv`, descargados con la API REST de GitHub el
9/11/2026 a las 10 p. m. (Bogotá). Uso: python3 metricas.py

Ítem = un PR. Inicio = el PR se abre (entra a verificación). Fin = se integra a main.
El repositorio NO registra cuándo empezó la construcción: los commits se hacen justo antes de abrir
el PR, así que el «tiempo de ciclo» que se puede medir es solo el de verificación.
"""
import csv
import statistics
from datetime import datetime, timedelta, timezone

BOGOTA = timezone(timedelta(hours=-5))
OBSERVACION = datetime(2026, 11, 9, 22, 0, tzinfo=BOGOTA)


def fecha(texto):
    return datetime.fromisoformat(texto.replace("Z", "+00:00")).astimezone(BOGOTA) if texto else None


with open("prs_2026-11-09.tsv", encoding="utf-8") as f:
    prs = list(csv.DictReader(f, delimiter="\t"))
with open("prs_tamano_2026-11-09.tsv", encoding="utf-8") as f:
    tam = {r["numero"]: r for r in csv.DictReader(f, delimiter="\t")}
for p in prs:
    p["creado"], p["integrado"], p["cerrado"] = fecha(p["creado"]), fecha(p["integrado"]), fecha(p["cerrado"])
    p["lineas"] = int(tam[p["numero"]]["adiciones"]) + int(tam[p["numero"]]["borrados"])
    p["commits"] = int(tam[p["numero"]]["commits"])
    p["bot"] = p["autor"].startswith("dependabot")

integrados = [p for p in prs if p["integrado"]]
retirados = [p for p in prs if p["cerrado"] and not p["integrado"]]
abiertos = [p for p in prs if not p["cerrado"]]
horas = lambda p: (p["integrado"] - p["creado"]).total_seconds() / 3600  # noqa: E731

print(f"PR en total: {len(prs)} · integrados {len(integrados)} · retirados {len(retirados)} · abiertos {len(abiertos)}")
inicio, fin = min(p["creado"] for p in prs), max(p["integrado"] for p in integrados)
dias = (fin - inicio).total_seconds() / 86400
print(f"Ventana: {inicio:%d/%m %H:%M} a {fin:%d/%m %H:%M} (Bogotá) = {dias:.2f} días")
print(f"Throughput medio: {len(integrados)}/{dias:.2f} = {len(integrados) / dias:.2f} PR integrados por día")

for nombre, grupo in (("Míos", [p for p in integrados if not p["bot"]]), ("Dependabot", [p for p in integrados if p["bot"]])):
    h = sorted(horas(p) for p in grupo)
    print(f"{nombre}: n={len(h)} · mediana {statistics.median(h) * 60:.0f} min · media {statistics.mean(h) * 60:.0f} min · máx {h[-1]:.1f} h")
todos = [horas(p) for p in integrados]
print(f"Todos: n={len(todos)} · mediana {statistics.median(todos) * 60:.0f} min · media {statistics.mean(todos):.2f} h")
sin_bloqueados = [horas(p) for p in integrados if horas(p) < 24]
print(f"Si se ocultan los 3 que esperaron días: media {statistics.mean(sin_bloqueados) * 60:.0f} min (n={len(sin_bloqueados)})")

instante = datetime(2026, 11, 5, 12, 0, tzinfo=BOGOTA)
wip = [p["numero"] for p in prs if p["creado"] <= instante and (p["cerrado"] is None or p["cerrado"] > instante)]
print(f"WIP el {instante:%d/%m %H:%M}: {len(wip)} → PR {', '.join(wip)}")
for p in abiertos:
    print(f"Edad de #{p['numero']} al {OBSERVACION:%d/%m %H:%M}: {(OBSERVACION - p['creado']).total_seconds() / 3600:.1f} h")

mios = [p for p in integrados if not p["bot"]]
con_retrabajo = [p for p in mios if p["commits"] > 1]
print(f"PR míos con más de un commit (correcciones durante la verificación): {len(con_retrabajo)} de {len(mios)}")
grandes = [p for p in mios if p["lineas"] >= 400]
chicos = [p for p in mios if p["lineas"] < 400]
for nombre, g in (("≥ 400 líneas", grandes), ("< 400 líneas", chicos)):
    print(f"  {nombre}: n={len(g)} · con varios commits {sum(p['commits'] > 1 for p in g)} · mediana {statistics.median(horas(p) for p in g) * 60:.0f} min")
