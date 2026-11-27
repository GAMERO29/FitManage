# Matriz inicial propuesta por la IA (copiada sin cambios; NO es la matriz vigente)

Prompt: «Con estos tres requisitos de FitManage (RF-03, RF-10 y RNF-05, pegados en su versión
v1.3) y la lista de carpetas del repositorio, arma una matriz requisito, componente, contrato y
prueba.»

| Requisito | Componente | Contrato | Prueba |
| --- | --- | --- | --- |
| RF-03 | `aplicacion/pagos.py` | registrarPago | `tests/nucleo/test_registro_pago.py::test_registra_pago_en_efectivo_sin_referencia` |
| RF-03 | `dominio/calculadora.py` | registrarPago | `tests/nucleo/test_calculadora.py::test_vencimiento_es_inicio_mas_duracion_menos_uno` |
| RF-10 | `aplicacion/anulacion.py` | anularPago | `tests/nucleo/test_anulacion.py::test_solo_el_administrador_puede_anular` |
| RF-10 | `aplicacion/pagos.py` | anularUltimoPago | `tests/integracion/api/test_api_pagos.py::test_anular_el_ultimo_pago_recalcula_la_membresia` |
| RNF-05 | `infraestructura/api/permisos.py` | reporteIngresos | `tests/integracion/api/test_api_reportes.py::test_la_recepcionista_no_ve_ingresos` |
| RNF-05 | `infraestructura/api/seguridad.py` | anularPago | `tests/integracion/api/test_api_pagos.py::test_la_recepcionista_recibe_403_al_anular` |
