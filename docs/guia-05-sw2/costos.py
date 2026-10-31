"""Ejercicio 3 · Costo mensual de FitManage distribuido en AWS frente al monolito.

Precios on-demand de us-east-1 consultados el 30/10/2026 (ver costos.md para las fuentes).
Ejecutar: python docs/guia-05-sw2/costos.py
"""

HORAS_MES = 730
TRM = 3185.01  # COP por USD, TRM del 23/10/2026

SERVICIOS = ["acceso", "socios", "membresias_y_cobros", "reportes"]
PRECIO = {
    "rds_db_t4g_micro_hora": 0.016,
    "rds_almacenamiento_gb_mes": 0.115,
    "nat_gateway_hora": 0.045,
    "nat_gateway_gb": 0.045,
    "ipv4_publica_hora": 0.005,
    "secrets_manager_secreto_mes": 0.40,
    "api_gateway_http_millon": 1.00,
}
GB_POR_BASE = 20
PETICIONES_MES = 30 * 600  # unas 300 consultas y 300 operaciones de otro tipo al día
GB_NAT_MES = 1


def costo_distribuido() -> list[tuple[str, float]]:
    n = len(SERVICIOS)
    return [
        (f"RDS PostgreSQL db.t4g.micro × {n}", n * PRECIO["rds_db_t4g_micro_hora"] * HORAS_MES),
        (f"Almacenamiento RDS {GB_POR_BASE} GB × {n}", n * GB_POR_BASE * PRECIO["rds_almacenamiento_gb_mes"]),
        ("NAT Gateway (horas)", PRECIO["nat_gateway_hora"] * HORAS_MES),
        (f"NAT Gateway ({GB_NAT_MES} GB procesado)", GB_NAT_MES * PRECIO["nat_gateway_gb"]),
        ("IPv4 pública del NAT", PRECIO["ipv4_publica_hora"] * HORAS_MES),
        (f"Secrets Manager × {n}", n * PRECIO["secrets_manager_secreto_mes"]),
        (f"API Gateway HTTP ({PETICIONES_MES:,} peticiones)", PETICIONES_MES / 1e6 * PRECIO["api_gateway_http_millon"]),
        ("Lambda (dentro de la capa gratuita)", 0.0),
    ]


def main() -> None:
    filas = costo_distribuido()
    total = sum(v for _, v in filas)
    for nombre, valor in filas:
        print(f"{nombre:<45} USD {valor:8.2f}")
    print(f"{'TOTAL distribuido':<45} USD {total:8.2f}  ≈ COP {total * TRM:,.0f}")
    ventas = 500
    margen = 0.20 * ventas
    print(f"Ventas de la MiPyme: USD {ventas}; margen operativo supuesto 20 %: USD {margen:.0f}")
    print(f"El costo distribuido es el {total / ventas:.1%} de las ventas y el {total / margen:.0%} del margen")


if __name__ == "__main__":
    main()
