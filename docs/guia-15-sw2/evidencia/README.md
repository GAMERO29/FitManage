# Evidencia de la Guía 15 (FPI-31)

## Inventario de deuda

`docs/deuda-tecnica.md`, sección «Revisión de la Guía 15»: los 15 ítems de la FPI-17 contra el sistema de hoy (8 pagados, 3 aceptados, 2 que empeoraron, 2 pendientes) y 8 ítems nuevos, DT-16 a DT-23. El roadmap de seis meses está en `docs/roadmap.md` y la decisión en el ADR N.° 15.

## Refactorización de DT-16 (lógica en los controladores)

- `pruebas-rama.txt`: la suite completa en la rama, con cobertura. 276 pruebas pasan, 1 se salta (QA-05 solo corre en PostgreSQL) y 1 falla a propósito (`xfail` estricto de DT-23). Cobertura total del 99 %; `aplicacion/socios.py`, `vistas.py` y `repositorios.py` al 100 %.
- `acoplamiento-vistas.txt`: lo que las vistas importaban antes y después. Antes llegaban a la calculadora del dominio, a la entidad `Socio` y a los repositorios de Django; ahora solo a `SolicitudPago` y `TipoDocumento`, que son datos de entrada. La complejidad ciclomática no cambió (A en las dos versiones): la deuda no era de complejidad, era de responsabilidad y acoplamiento.
- La prueba `test_los_controladores_no_hacen_el_trabajo_de_los_casos_de_uso` en `tests/nucleo/test_arquitectura.py` falla si una vista vuelve a importar la calculadora o los repositorios. La versión anterior de `vistas.py` importaba los dos módulos, así que la regla la habría detenido.
- Las pruebas de la API de socios, de contrato y de aceptación pasan sin cambios: el comportamiento visible es el mismo.

## Ejercicio 5 (IA)

- `ia-codigo-tal-cual.txt`: las 14 pruebas que fallan con la refactorización de la IA aplicada sin cambios.
- `ia-codigo-con-fk-corregida.txt`: con un solo arreglo la suite pasa, pero la respuesta 422 que inventó la IA rompe el contrato.
- `ia-migracion-generada.py.txt`: la migración que exigía su modelo (borra la tabla `idempotencia`).
- Auditoría completa: [`../ejercicio-ia/README.md`](../ejercicio-ia/README.md).
