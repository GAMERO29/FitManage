# Guion del video demo (máximo 5 minutos)

Guía 16 (FPI-32). Todo lo que se muestra existe en el repositorio o en producción. Antes de grabar:

1. En Render → servicio web → **Environment**, crea `FITMANAGE_ADMIN_NOMBRE`, `FITMANAGE_ADMIN_CORREO` y `FITMANAGE_ADMIN_CLAVE` (mínimo 12 caracteres). Guarda y deja que el servicio se despliegue de nuevo. En los logs debe aparecer «Administrador: se creó la cuenta de …». La clave no se escribe en ningún chat ni archivo.
2. Abre `https://fitmanage-svol.onrender.com/` un minuto antes: el plan gratuito se duerme y el primer arranque tarda.
3. Usa solo datos inventados (por ejemplo, CC 1090000001, «Ana Prueba», 3001234567). El aviso de privacidad todavía no está aprobado (DT-10).

| Tiempo | Qué se muestra | Qué se dice (idea, no libreto) |
| --- | --- | --- |
| 0:00–0:30 | La pantalla de inicio de sesión en producción. | El problema de la FPI-01: en hora pico, recepción no sabe si una persona pagó y la fila crece. FitManage responde eso en dos segundos. |
| 0:30–1:45 | Iniciar sesión. Consultar un documento que no existe → «No está registrado» → registrar al socio → «Sin membresía» → registrar un pago Mensual por Nequi con comprobante → «Puede entrar, le quedan 30 días». | El flujo crítico real: CU-02, CU-03 y CU-04. Las fechas y el valor los calcula el servidor (RN-03, RN-04). Si se pulsa dos veces «Confirmar pago», se registra un solo pago (PA-11). |
| 1:45–2:15 | Consultar el mismo socio desde el celular. | La misma pantalla funciona en el celular del personal (RNF-03). El documento se ve enmascarado: la consulta no expone datos personales (FPI-22). |
| 2:15–3:15 | GitHub: un PR con los nueve checks requeridos, la regla de `main` y el release v1.0.0. | Ningún cambio entra a `main` sin pasar las pruebas, el contrato, SonarCloud, Semgrep, Trivy, el escaneo de secretos y, desde esta guía, las licencias. |
| 3:15–4:15 | El tablero de Grafana Cloud de producción y el postmortem del simulacro. | Defensa del ADR N.° 05 (no distribuir): 10 recepcionistas simultáneas dan un p95 de 13,5 ms; lo que sí falla es la base de datos, y un microservicio más no lo arregla. El SLO de 99,5 % y lo que consumió el simulacro de 30 minutos (30 % del presupuesto). |
| 4:15–5:00 | `docs/deuda-tecnica.md` y `docs/roadmap.md`. | Lo que queda pendiente, dicho sin rodeos: la base gratuita vence el 2/12/2026, falta el aviso de privacidad y no hay pantalla para crear planes ni personal. Cada pendiente tiene fecha y disparador. |

Al terminar, pega el enlace del video en la FPI-32 (sección B) y en el README.
