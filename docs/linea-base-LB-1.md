# Línea base LB-1 del MVP heredado

ISO/IEC/IEEE 12207 · proceso de gestión de la configuración. Esta línea base es el punto de partida medible para la evolución de FitManage en Ingeniería de Software II. Solo cambia mediante Pull Request revisado que referencie un ítem del inventario de deuda (`deuda-tecnica.md`) o una solicitud de cambio.

| Campo | Valor |
| --- | --- |
| Identificador | LB-1 (etiqueta Git `LB-1`) |
| Commit | `a2a0f3a` · rama `main` |
| Fecha | 30/10/2026 |
| Elementos de configuración | `dominio/` (6 módulos), `tests/` (48 pruebas), `prototipo/FitManage_Prototipo.html` (v1.0), `pyproject.toml`, `requirements-dev.txt` |
| Documentos asociados | ERS, DAD y DDS de FitManage; FPI-12 (núcleo y deuda DT-01 a DT-03) |
| Responsable | Juan Sebastián Cárdenas Acevedo |

## Métricas de calidad del núcleo de dominio

| Métrica | Herramienta | Valor medido | Umbral |
| --- | --- | --- | --- |
| Tamaño | radon raw | 257 SLOC · 56 bloques (clases y métodos) | — |
| Complejidad ciclomática promedio | radon cc | 1,89 (A) | ≤ 5 |
| Complejidad ciclomática máxima | radon cc | 5 · `RegistroPagoService._validar_referencia` | ≤ 10 |
| Bloques con complejidad > 10 | radon cc | 0 | 0 |
| Índice de mantenibilidad | radon mi | servicios 52,2 · calculadora 49,6 · modelos 38,6 (todos A) | ≥ 20 |
| Pruebas automatizadas | pytest | 48 aprobadas · 0 fallidas · 0,07 s | 100 % aprobadas |
| Cobertura de líneas | pytest-cov | 98 % (211 sentencias, 2 sin cubrir) | ≥ 95 % |
| Cobertura de ramas | pytest-cov | 30 de 32 ramas | — |
| Estilo y errores | ruff (E, F, W, I, B, UP, SIM) | 0 hallazgos | 0 |
| Fechas sin zona horaria | ruff DTZ001 | 13 hallazgos (todos en `tests/`) | 0 |
| Calidad general | pylint 4.1 | 8,64/10 (16 docstrings faltantes, `Pago` con 15 atributos, 2 servicios con un solo método público) | ≥ 8 |
| Seguridad del código | bandit 1.9 | 0 hallazgos en 289 líneas | 0 altos |
| Vulnerabilidades de dependencias | pip-audit | 0 (el dominio no tiene dependencias de ejecución) | 0 |
| Licencias | metadatos PyPI | pytest, pytest-cov, ruff y radon: MIT · bandit: Apache-2.0 | Sin GPL |

## Métricas del prototipo navegable

| Métrica | Herramienta | Valor medido |
| --- | --- | --- |
| Tamaño | lizard (JavaScript) | 378 líneas del archivo · 284 NLOC de script · 34 funciones |
| Complejidad promedio | lizard | 2,6 |
| Funciones con complejidad > 10 | lizard | 1 · manejador de clics (líneas 348–372), CCN = 23 |
| Reglas de negocio duplicadas en la interfaz | revisión manual | RN-03, RN-04, RN-05 y RN-06 (ver DT-04) |
| Control de acceso | revisión manual | solo en el navegador (ver DT-05) |

## Estado de la arquitectura frente al DAD

| Capa del DAD | Estado en LB-1 |
| --- | --- |
| Dominio | Implementada y probada: `Socio`, `Plan`, `Pago`, `Usuario`, enumeraciones, `CalculadoraMembresia`, `RegistroPagoService`, `AnulacionPagoService`, 4 puertos. |
| Aplicación | Sin implementar: no hay `RegistroSocio`, `ReporteIngresos`, autorización por rol ni transacciones. |
| Infraestructura | Sin implementar: no hay repositorios ORM, `RelojBogota`, auditoría ni respaldos. |
| Presentación | Solo el prototipo HTML con datos fijos; no existe la aplicación Django. |
| Operación | Repositorio en GitHub y flujo `Calidad` en GitHub Actions creados en esta línea base; sin entorno de despliegue. |

## Cómo reproducir las mediciones

```bash
pip install -r requirements-dev.txt lizard pylint pip-audit
radon cc -s -a dominio && radon mi -s dominio && radon raw -s dominio
pytest --cov=dominio --cov-branch --cov-report=term-missing
ruff check . && ruff check dominio tests --select DTZ --statistics
pylint dominio --disable=C0114
bandit -r dominio
pip-audit -r requirements-dev.txt
lizard -l javascript prototipo/
```
