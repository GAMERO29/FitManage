# Revisión de diseño simulada · requisitos v1.3

| Campo | Valor |
| --- | --- |
| Fecha | 27/11/2026 |
| Material revisado | [`requisitos-v1.3.md`](requisitos-v1.3.md), [`matriz.md`](matriz.md), [`secuencia_registrar_pago.png`](secuencia_registrar_pago.png), ERS 1.0, ADR N.° 18, `docs/api/openapi.yaml` 1.8.0 |
| Revisores | Juan Sebastián Cárdenas Acevedo, más un rol de «equipo revisor» simulado por la misma persona con la lista de verificación de abajo. **No hubo otro equipo real.** |
| Lista de verificación | 1) ¿Cada requisito tiene componente, operación y prueba? 2) ¿El texto del requisito coincide con lo que hace el código? 3) ¿Cada regla vive en un solo lugar del diseño? |

## Hallazgos

| ID | Hallazgo | Severidad | Impacto | Estado y cierre |
| --- | --- | --- | --- | --- |
| H-10-01 | La ERS 1.0 (RN-07, RF-10, RNF-05 y CA-13) dice que solo el administrador anula. El ADR N.° 18 (9/11) dejó que la recepcionista corrija sus pagos del mismo día y el código lo hace, pero nadie versionó los requisitos. | Media: el piloto se validaría contra un texto que el sistema no cumple | ERS, matriz, criterios de aceptación CA-13 y CP-10c | **Cerrado.** RF-10 y RNF-05 pasan a v1.3. Evidencia vinculada: `test_frontera_la_recepcionista_corrige_hasta_la_medianoche_de_bogota` y `test_la_recepcionista_no_anula_lo_que_registro_otra_persona`. Pendiente aparte: actualizar el documento de la ERS del proyecto. |
| H-10-02 | El motivo de anulación «con al menos 5 caracteres» existe en el contrato (`minLength: 5`) y en la pantalla (`app.js`, líneas 520 y 557), pero el dominio acepta un solo carácter. Otro consumidor, como un comando, podría anular con «x». | Baja hoy, alta si aparece otro consumidor | `dominio/modelos.py`, contrato y pantalla | **Abierto → CR-02.** |

## Solicitud de cambio CR-02

| Campo | Valor |
| --- | --- |
| Solicitud | Que la regla «motivo con al menos 5 caracteres» viva en el dominio (RN-07 v1.4) y se aplique igual en anular el último pago, anular por id y cambiar de plan. |
| Origen | H-10-02 |
| Impacto | Código: `Pago.anular` (un lugar en el Domain Model). Contrato: ninguno, ya exige `minLength: 5`. Pantalla: ninguno. Pruebas: una nueva en el núcleo y revisar las que anulan con motivos cortos. Requisitos: RN-07 y RF-10 pasan a v1.4. Datos: los pagos ya anulados no cambian, porque la regla solo aplica a anulaciones nuevas. |
| Riesgo | Bajo: la API ya rechazaba motivos cortos, así que no cambia nada para la pantalla. |
| Decisión | **Aceptada** (27/11/2026). Se implementa en la Guía 12, donde además sirve como el cambio de regla del experimento Transaction Script contra Domain Model. |
| Prueba que la cierra | `tests/nucleo/test_anulacion.py::test_un_motivo_de_menos_de_5_caracteres_no_anula` |
| Versiones | Requisitos v1.3 → v1.4 al cerrar. Contrato 1.8.0 sin cambio. |
