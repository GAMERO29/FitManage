# Evidencia del pipeline y del Quality Gate (FPI-25)

| Qué | Resultado | Enlace |
| --- | --- | --- |
| PR #5: pipeline nuevo | Los 5 jobs en verde; `QUALITY GATE STATUS: PASSED` | https://github.com/GAMERO29/FitManage/actions/runs/41511094936 |
| Primer push a `main` con el pipeline | Los 5 jobs en verde; 210 pruebas en la imagen, cobertura 100 %, humo k6 p95 6,6 ms; imagen `ghcr.io/gamero29/fitmanage:sha-469c37651f6dfff68afca5f105c878c60e6ad092`, digest `sha256:56e261c281637d11d2f2efffe05f91076327b99263f049f78e70c70f98cce26b` | https://github.com/GAMERO29/FitManage/actions/runs/41511728555 |
| Push directo a `main` con una llave con formato de Stripe | Rechazado por el push protection de GitHub | [`push-proteccion-secretos.txt`](push-proteccion-secretos.txt) |
| Push directo a `main` con la regla activa | Rechazado: «Changes must be made through a pull request» | [`push-directo-a-main.txt`](push-directo-a-main.txt) |
| PR #6, intento 1: función sin pruebas, complejidad 12 y llave en el código | `linter` en rojo (bandit B105); los jobs que dependen de él no corren; unión rechazada con 405 | https://github.com/GAMERO29/FitManage/actions/runs/41516586537 · [`merge-pr6-rechazado.txt`](merge-pr6-rechazado.txt) |
| PR #6, intento 2: limpio para el linter, todavía sin pruebas | `linter`, `pruebas` (98,7 % total) y `artefacto` en verde; `analisis` en rojo: 0 % de cobertura en el código nuevo (Sonar way exige 80 %); unión rechazada con 405 | https://github.com/GAMERO29/FitManage/actions/runs/41516890066 · [`merge-pr6-rechazado-2.txt`](merge-pr6-rechazado-2.txt) |

El PR #6 se cerró sin unir. Su rama `demo/puerta-de-calidad` se conserva como evidencia.
