# Guía II-04 · Calidad y pruebas del incremento de auditoría

Versión evaluada: `c07c2d3` (main después de la Guía II-03).

- `mutaciones.py`: 9 mutaciones sobre una copia del repositorio; `mutaciones_salida_antes.txt` (sobreviven M8 y M9) y `mutaciones_salida_despues.txt` (mueren las 9 con las pruebas nuevas).
- `fallo_controlado.sh` y `.txt`: el worker de gunicorn muere entre el UPDATE del pago y el INSERT del evento; no queda nada guardado y el reintento funciona.
- `k6_auditoria.txt`: `pruebas_carga/consulta_auditoria.js` con 30.000 eventos (`pruebas_carga/sembrar_auditoria.py`), 5 usuarios, 2 minutos.
- `accesibilidad.js` y `axe_salida.txt`: axe-core 4.10.2 (WCAG 2.1 A y AA) en cuatro pantallas.
- `suite_postgresql.txt` y `suite_sqlite.txt`: resultados de la suite completa con cobertura.
