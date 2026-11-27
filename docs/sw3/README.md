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
| ADR N.° 20 | Decisión pendiente de la Guía 01: bloquear TRUNCATE sobre la auditoría (DEF-03). |

## Línea base

LB-SW3-01 es el commit `1790310` de `main` (v1.1.0 más las correcciones H-01 a H-03 de la Guía II-06), el mismo que estaba desplegado en Render al empezar.
