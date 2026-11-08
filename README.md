# FitManage

Sistema integrado para el manejo y la gestión de gimnasios MiPyme de Cúcuta: membresías, pagos y consulta de acceso en recepción.

Proyecto integrador de Ingeniería de Software II · Universidad de Pamplona · Juan Sebastián Cárdenas Acevedo.

## Contenido

| Carpeta | Qué contiene |
| --- | --- |
| `dominio/` | Núcleo de reglas de negocio en Python puro (RN-01 a RN-10): entidades, `CalculadoraMembresia`, servicios y puertos. |
| `aplicacion/` | Casos de uso (registrar socio, consultar estado, registrar, previsualizar y anular pagos, cambiar precios). |
| `tests/` | Suite de pytest: núcleo con dobles en memoria, integración con la base real, contrato OpenAPI y Pact, aceptación (PA-xx). |
| `prototipo/` | Prototipo original de la Guía 4 (HTML autónomo, datos de ejemplo). Se conserva como evidencia de diseño; el aplicativo real está en `infraestructura/web/`. |
| `infraestructura/` | Adaptadores: API `/api/v1`, persistencia con Django ORM, observabilidad y el aplicativo del personal (`web/`, ADR N.° 16 y 17). |
| `docs/` | ADR N.° 01 a 17, inventario de deuda, roadmap, runbooks, postmortems, evidencia de cada guía y el [Dossier Técnico Final](docs/Dossier_Final.md). |

## En producción

- Aplicativo del personal: https://fitmanage-svol.onrender.com. Recepción, registro de socios y pagos, vencimientos con WhatsApp y, para el administrador, historial con anulación, reportes, precios de los planes y cuentas del personal.
- La primera cuenta de administrador se crea al arrancar desde `FITMANAGE_ADMIN_NOMBRE`, `FITMANAGE_ADMIN_CORREO` y `FITMANAGE_ADMIN_CLAVE`, configuradas en el panel de Render (`preparar_gimnasio`).

## Ejecutar las pruebas

```bash
python -m venv .venv && source .venv/bin/activate   # En Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest --cov
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
