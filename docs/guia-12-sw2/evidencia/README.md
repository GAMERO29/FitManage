# Evidencia de la Guía 12 (FPI-28)

El repositorio es público, así que aquí solo quedan conteos y decisiones. Los reportes completos están en el panel **Security → Code scanning** del repositorio (solo lo ven sus administradores) y como artefacto privado `reporte-trivy-imagen` de cada corrida del workflow `Seguridad`, durante 30 días.

## Corridas del workflow `Seguridad` (PR #14)

| Corrida | Commit | Resultado | Qué pasó |
| --- | --- | --- | --- |
| 41578720201 | `4a40209` | Rojo | `sast`, `sca-dependencias` y `sca-imagen` no arrancaron: el SHA fijado de `github/codeql-action` tenía un carácter de más. `secretos` sí corrió y encontró 7 tokens JWT: 2 de ejemplo en el contrato y 5 reales, ya vencidos, en los resúmenes de k6. |
| 41579742854 | `e58cf75` | Rojo | `sast`, `sca-dependencias` y `secretos` en verde. `sca-imagen` en rojo: 45 CVE altos en paquetes de Debian. |
| 41580868707 | `0984514` | **Verde** | La imagen ya no trae pip ni binarios setuid, y los 8 CVE sin parche quedaron aceptados con razón y vencimiento. |

Semgrep también corrió en local antes del primer push. Sus hallazgos (un `curl | python3` en el pipeline y un `checkout` del código de un PR en un workflow con secretos, entre otros) se corrigieron en el commit `4a40209`.

## Imagen de producción (Trivy, `fitmanage:escaneo`)

| | Antes (41579742854) | Después (41580868707) |
| --- | --- | --- |
| Paquetes de Debian 13 | 185 CVE: 45 altos, 72 medios, 61 bajos, 7 sin clasificar | 140 CVE: 0 altos (8 aceptados en `.trivyignore`), 72 medios, 61 bajos, 7 sin clasificar |
| Paquetes de Python | 12 CVE, todos de pip 25.0.1 (en `/opt/venv` y en `/usr/local`) | 0: pip ya no está en la imagen |
| Puerta (`--severity CRITICAL,HIGH --exit-code 1`) | Falla | Pasa |

Los 45 altos eran 8 CVE repetidos en varios paquetes de la misma familia (util-linux, ncurses, systemd). La razón de cada uno está en [`.trivyignore`](../../../.trivyignore).

## Código y repositorio

- **Semgrep:** 421 reglas sobre 65 archivos, 0 hallazgos abiertos. 13 están suprimidos con `nosemgrep` y su razón en la misma línea; no se suben al panel Security para que no aparezcan como alertas abiertas.
- **Trivy, dependencias:** `requirements.txt` sin CVE. Las dependencias de desarrollo de la vista móvil (Pact) van al reporte, pero no a la puerta.
- **Trivy, secretos:** 0 secretos. En la primera corrida aparecieron dos tipos: tokens JWT (ya vencidos) en los resúmenes de k6, que se reemplazaron en `e58cf75`, y los JWT de ejemplo del contrato OpenAPI, que se permiten con una regla en [`trivy-secret.yaml`](../../../trivy-secret.yaml).

## Workflow de la IA (Ejercicio 5)

[`demo-ia-escaneo.txt`](demo-ia-escaneo.txt) es un extracto de la corrida 41581413862, en la que el workflow de la IA corrió sin cambios en el PR #15 (cerrado sin fusionar). Semgrep 1.100.0 ni siquiera arranca, Trivy 0.56.2 no entiende las reglas de configuración actuales y GitHub avisa que las acciones apuntan a Node.js 20.
