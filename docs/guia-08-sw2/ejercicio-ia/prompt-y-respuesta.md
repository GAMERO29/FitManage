# Ejercicio 5 · Script de k6 generado por IA para la consulta de estado

**Herramienta:** Claude (Anthropic), en una conversación sin el contrato ni el repositorio. **Fecha:** 2/11/2026.

## Prompt

> Genera un script de k6 para hacer una prueba de carga del endpoint que consulta el estado de membresía de un socio en mi API de gimnasio (FitManage). La API usa JWT.

## Respuesta de la IA (sin modificar)

El script completo está en [`script-ia.js.txt`](script-ia.js.txt), con extensión `.txt` para que nadie lo corra por error. **Nunca se ejecutó tal como vino.** El texto que lo acompañaba:

> Este script simula una carga realista y exigente: sube a 1000 usuarios virtuales, los sostiene tres minutos y termina con un pico de estrés de 5000 para encontrar el punto de quiebre de tu API. Cada usuario virtual inicia sesión para obtener su token JWT, igual que haría un usuario real, y consulta el estado de una cédula aleatoria. El umbral de p95 < 500 ms es un estándar de la industria para APIs. Cambia `BASE_URL` por la URL de tu servidor y ejecuta `k6 run script.js`.

## Auditoría y corrección

La tabla de hallazgos está en el Ejercicio 5 de la guía resuelta. El script corregido es [`pruebas_carga/consulta_estado.js`](../../../pruebas_carga/consulta_estado.js), y la medición del patrón de «iniciar sesión en cada iteración» está en [`login-por-iteracion.txt`](login-por-iteracion.txt).
