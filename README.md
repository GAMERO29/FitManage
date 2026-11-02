# FitManage

Sistema integrado para el manejo y la gestión de gimnasios MiPyme de Cúcuta: membresías, pagos y consulta de acceso en recepción.

Proyecto integrador de Ingeniería de Software I y II · Universidad de Pamplona · Juan Sebastián Cárdenas Acevedo.

## Contenido

| Carpeta | Qué contiene |
| --- | --- |
| `dominio/` | Núcleo de reglas de negocio en Python puro (RN-01 a RN-10): entidades, `CalculadoraMembresia`, servicios y puertos. |
| `tests/` | 48 pruebas automatizadas con pytest, con repositorios en memoria y reloj fijo. |
| `prototipo/` | Prototipo funcional navegable del MVP (HTML autónomo, datos de ejemplo). |
| `infraestructura/` | Adaptadores técnicos que implementan los puertos del dominio (por ahora, `RelojBogota`). |
| `docs/` | Línea base técnica, inventario de deuda técnica y registros de decisión arquitectónica (ADR). |

## Ejecutar las pruebas

```bash
python -m venv .venv && source .venv/bin/activate   # En Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest --cov=dominio
```

## Con Docker (PostgreSQL 16 + la API con gunicorn, ADR N.° 10)

```bash
cp .env.example .env        # y cambie las tres claves (openssl rand -hex 32)
docker compose up -d --build
curl http://127.0.0.1:8000/api/v1/salud
docker compose --profile pruebas run --rm pruebas   # la suite completa contra ese PostgreSQL
docker compose down          # los datos quedan en el volumen "datos"; down -v los borra
```

La imagen de producción (`docker build --target produccion`) pesa 206 MB, corre como el usuario 10001 y no trae las pruebas ni las herramientas de desarrollo. El pipeline publica cada versión de `main` en `ghcr.io/gamero29/fitmanage`.
