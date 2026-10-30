# FitManage

Sistema integrado para el manejo y la gestión de gimnasios MiPyme de Cúcuta: membresías, pagos y consulta de acceso en recepción.

Proyecto integrador de Ingeniería de Software I y II · Universidad de Pamplona · Juan Sebastián Cárdenas Acevedo.

## Contenido

| Carpeta | Qué contiene |
| --- | --- |
| `dominio/` | Núcleo de reglas de negocio en Python puro (RN-01 a RN-10): entidades, `CalculadoraMembresia`, servicios y puertos. |
| `tests/` | 48 pruebas automatizadas con pytest, con repositorios en memoria y reloj fijo. |
| `prototipo/` | Prototipo funcional navegable del MVP (HTML autónomo, datos de ejemplo). |
| `docs/` | Línea base técnica, inventario de deuda técnica y registros de decisión arquitectónica (ADR). |

## Ejecutar las pruebas

```bash
python -m venv .venv && source .venv/bin/activate   # En Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest --cov=dominio
```
