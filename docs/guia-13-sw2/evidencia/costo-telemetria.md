# Cuánto cuesta la telemetría (medición local, 3/11/2026)

Misma máquina, misma base sembrada con el volumen de QA-01 (2.000 socios y 20.000 pagos en PostgreSQL 16), gunicorn con 1 proceso y 4 hilos, y el script de k6 `pruebas_carga/consulta_estado.js` con 10 usuarios durante 90 s (996 consultas en cada corrida, ninguna con error). Las trazas se mandan a un colector OTLP falso que acepta todo, para incluir el costo de serializarlas y enviarlas.

| Configuración | p50 | p95 | CPU del proceso (incluye el arranque) | Logs escritos |
| --- | --- | --- | --- | --- |
| Telemetría apagada (`FITMANAGE_TELEMETRIA=0`) | 10,64 ms | 14,31 ms | 9,21 s | 232.854 bytes |
| Encendida, muestreo del 10 % (lo que va a producción) | 11,04 ms | 16,78 ms | 9,74 s (+5,8 %) | 675.170 bytes |
| Encendida, muestreo del 100 % | 11,14 ms | 17,84 ms | 10,10 s (+9,7 %) | 674.270 bytes |

Lectura:

- Con este tráfico, la latencia casi no cambia: la mediana sube 0,4 ms y el p95 varía entre corridas más de lo que cambia por la telemetría. QA-01 pide p95 < 2 s.
- La CPU sí lo nota: pasar del 10 % al 100 % de trazas casi duplica el sobrecosto. Por eso se muestrea.
- Los logs triplican su tamaño: unos 680 bytes por consulta (una línea de la consulta y una de la petición). Con 500 consultas al día, que ya es un día de mucho movimiento para un gimnasio pequeño, son unos 340 KB diarios: menos de 2,5 MB en los 7 días que Render guarda los logs.
- Con la telemetría apagada se sigue escribiendo la línea de la consulta de estado, porque está en la vista. Lo que se apaga es el middleware: el span de la petición, la métrica de latencia y la línea de cada petición.

Los scripts están en [`medicion/`](medicion/): `colector_falso.py` y `medir.sh`, que arranca gunicorn, corre k6 y lee el tiempo de CPU del worker en `/proc/<pid>/stat` antes de apagarlo.
