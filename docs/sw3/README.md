# Software III sobre FitManage

Evidencias de las guías de Ingeniería de Software III aplicadas al MVP heredado de Software II. Las fichas resueltas (FPI-III-01 a 16) están fuera del repositorio; aquí quedan los scripts, salidas, diagramas y decisiones que esas fichas citan.

Todo se ejecuta en un laboratorio local con datos ficticios (Ana Prueba Demo, CC 1090000011). Nada de esto corre contra producción: la auditoría no se puede borrar.

| Pieza | Para qué |
| --- | --- |
| `laboratorio.sh` | Base PostgreSQL nueva y gunicorn con el commit actual en `127.0.0.1:8765`. |
| `recorrido_base.py` y su salida | Recorrido de línea base de la Guía 01 (12 pasos, RF-01, RF-03, RF-04, RF-10, RN-06 y auditoría). |
| `g02/` | Vistas lógica y física (`.mmd` editables y `.png`) y el recorrido con la base detenida. |
| `g03/` | Pruebas de caracterización antes y después de introducir `PoliticaAnulacion` (Strategy). |
| `g04/registro_cambio.md` | CR-01 por línea base y por incrementos, y la revisión simulada. |
| `g05/` | Mapa de importaciones antes y después de sacar el ORM de `GET /planes` y la regla de arquitectura que lo vigila. |
| `g06/` | `DELETE /socios/{tipo}/{numero}` por los tres caminos (204, 409 y 503 con la base detenida) y capturas de la interfaz. |
| `g07/` | `mapa_dependencias.py` (ciclos y nombres privados), el ciclo api ↔ consultas antes y después, y el contrato compartido doble/ORM. |
| `g08/` | Objeto de valor `Periodo`, la invariante del pago antes y después, diagramas de clases y de secuencia. |
| `g09/` | Prueba de contrato de `CorreoSaliente` para todas sus variantes: las 7 fallas de «éxito falso» y su corrección. |
| `g10/` | Requisitos v1.3 congelados, matriz trazable (la vigila `tests/nucleo/test_trazabilidad.py`), revisión simulada con CR-02 y la matriz de la IA con 5 referencias inexistentes. |
| `g11/` | Glosario, invariantes I-1 a I-6, el agregado `HistorialPagos` y su prueba de atomicidad. |
| `g12/` | Experimento Transaction Script contra Domain Model con casos equivalentes, impacto de CR-02 y ADR N.° 21. |
| `g13/` | Especificación `PUEDE_ANULAR`, opciones y capturas antes y después del botón «Anular» para dos recepcionistas homónimas. |
| `g14/` | Anulación de extremo a extremo: estados de la pantalla, migración 0004 (TRUNCATE) y pruebas de atomicidad, repetición y permanencia tras reinicio. |
| ADR N.° 20 | Bloquear TRUNCATE sobre la auditoría (DEF-03). Propuesto en la Guía 01 y aceptado en la Guía 14. |

## Línea base

LB-SW3-01 es el commit `1790310` de `main` (v1.1.0 más las correcciones H-01 a H-03 de la Guía II-06), el mismo que estaba desplegado en Render al empezar.
