# Auditoría de IA · Guía 10 (matriz inicial)

**Prompt.** «Con estos tres requisitos de FitManage (RF-03, RF-10 y RNF-05, pegados en su versión
v1.3) y la lista de carpetas del repositorio, arma una matriz requisito, componente, contrato y
prueba.» Solo texto de requisitos y nombres de carpetas; sin datos ni secretos.

**Salida.** [`matriz_ia.md`](matriz_ia.md), seis filas.

**Criterio de verificación.** El mismo de la prueba `tests/nucleo/test_trazabilidad.py`: cada
componente existe, cada operación está en el contrato y cada prueba está definida. Lo corrí con
`verificar_matriz.py` ([`verificacion_ia.txt`](verificacion_ia.txt)): **5 referencias no existen.**

| Referencia de la IA | Qué pasó |
| --- | --- |
| `aplicacion/anulacion.py`, `infraestructura/api/permisos.py` | Archivos inventados a partir de nombres plausibles. |
| Operación `anularUltimoPago` | No existe en el contrato: la anulación es `PATCH /pagos/{pagoId}` (`anularPago`). |
| `test_solo_el_administrador_puede_anular` | Prueba inventada y, además, **supuesto no sustentado**: aunque le di RF-10 v1.3, la IA siguió con la regla de v1.2 («solo el administrador»). El ADR N.° 18 la cambió. |
| `test_la_recepcionista_recibe_403_al_anular` | Prueba inventada; las reales son `test_la_recepcionista_no_anula_un_pago_de_otro_dia` y `..._lo_que_registro_otra_persona`. |

**Corrección.** La matriz vigente ([`matriz.md`](matriz.md)) se armó desde el código y
`verificar_matriz.py` da 0 referencias inexistentes. Para que no vuelva a pasar, la prueba de
trazabilidad corre en cada push.

**Limitación.** La misma sesión generó y auditó la matriz.
