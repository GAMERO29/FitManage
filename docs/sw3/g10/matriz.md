# Matriz de diseño trazable · requisitos v1.3

Cada fila une un requisito versionado con el componente que lo implementa, la operación del
contrato (`operationId` de `docs/api/openapi.yaml`) y las pruebas que lo verifican. La prueba
`tests/nucleo/test_trazabilidad.py` lee esta tabla en cada push y falla si un archivo, una
operación o una prueba de la tabla no existe.

Revisores: Juan Sebastián Cárdenas Acevedo (autor) · revisión simulada en [`revision.md`](revision.md).

| Requisito | Componente | Contrato | Prueba |
| --- | --- | --- | --- |
| RF-03 v1.2 · cálculo del periodo (RN-03, RN-04) | `dominio/calculadora.py` | registrarPago | `tests/nucleo/test_registro_pago.py::test_trimestral_desde_el_primero_de_marzo_vence_el_29_de_mayo`, `tests/nucleo/test_calculadora.py::test_renovar_el_mismo_dia_del_vencimiento_inicia_manana`, `tests/integracion/api/test_api_pagos.py::test_renovacion_anticipada_no_pierde_dias` |
| RF-03 v1.2 · comprobante (RN-06) | `aplicacion/pagos.py` | registrarPago | `tests/nucleo/test_registro_pago.py::test_referencia_duplicada_en_pago_vigente_se_rechaza`, `tests/integracion/test_concurrencia_postgres.py::test_qa05_nunca_quedan_dos_pagos_vigentes_con_la_misma_referencia` |
| RF-03 v1.2 · precio completo (RN-08) | `aplicacion/pagos.py` | registrarPago | `tests/nucleo/test_registro_pago.py::test_el_pago_copia_valor_y_duracion_del_plan`, `tests/integracion/api/test_api_pagos.py::test_el_cliente_no_puede_mandar_fechas_ni_valor` |
| RF-03 v1.2 · un solo pago por clic | `infraestructura/api/seguridad.py` | registrarPago | `tests/integracion/api/test_api_pagos.py::test_doble_clic_con_la_misma_clave_crea_un_solo_pago` |
| RF-10 v1.3 · solo el último vigente | `aplicacion/pagos.py` | anularPago | `tests/nucleo/test_anulacion.py::test_por_id_no_deja_anular_un_pago_que_no_es_el_ultimo`, `tests/integracion/api/test_api_pagos.py::test_no_se_anula_un_pago_que_no_es_el_ultimo` |
| RF-10 v1.3 · la recepcionista corrige su día | `dominio/politicas.py` | anularPago | `tests/nucleo/test_anulacion.py::test_la_recepcionista_anula_lo_que_ella_registro_hoy`, `tests/nucleo/test_periodo_y_transiciones.py::test_frontera_la_recepcionista_corrige_hasta_la_medianoche_de_bogota`, `tests/integracion/api/test_api_pagos.py::test_la_recepcionista_no_anula_un_pago_de_otro_dia` |
| RF-10 v1.3 · se conserva y se audita | `dominio/modelos.py` | anularPago | `tests/nucleo/test_anulacion.py::test_el_pago_anulado_no_se_borra`, `tests/integracion/api/test_api_auditoria_pagos.py::test_anular_deja_el_motivo_y_quien_registro_el_pago` |
| RF-10 v1.3 · una sola vez, aun en paralelo | `infraestructura/api/vistas.py` | anularPago | `tests/integracion/api/test_api_concurrencia_socio.py::test_d01_dos_anulaciones_del_mismo_pago_solo_una_tiene_exito` |
| RNF-05 v1.3 · reportes | `infraestructura/api/seguridad.py` | reporteIngresos | `tests/integracion/api/test_api_reportes.py::test_la_recepcionista_no_ve_ingresos` |
| RNF-05 v1.3 · anulación ajena o vieja | `dominio/politicas.py` | anularPago | `tests/nucleo/test_anulacion.py::test_la_recepcionista_no_anula_lo_que_registro_otra_persona`, `tests/nucleo/test_anulacion.py::test_la_recepcionista_no_anula_un_pago_de_ayer` |
| RNF-05 v1.3 · supresión y cuentas | `infraestructura/api/seguridad.py` | suprimirSocio | `tests/integracion/api/test_api_supresion_socio.py::test_la_recepcionista_no_suprime`, `tests/integracion/api/test_api_administracion.py::test_la_recepcionista_no_administra_cuentas` |
| RNF-05 v1.3 · un rechazo no cambia nada | `infraestructura/api/seguridad.py` | anularPago | `tests/integracion/api/test_api_auditoria_pagos.py::test_un_rechazo_no_deja_evento` |
