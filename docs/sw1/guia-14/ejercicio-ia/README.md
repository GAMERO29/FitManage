# Guía 14 (FPI-14) · Pruebas unitarias generadas por IA para `CalculadoraMembresia`

- **IA:** Claude Haiku, con el código de `dominio/calculadora.py`. Prompt y respuesta sin editar en esta carpeta; el archivo de pruebas extraído es `test_calculadora_ia.py`.
- **Corridas:** `corrida-tal-cual.txt` (sin cambios) y `mutantes.txt` (con el import corregido).

| Pregunta de la guía | Hallazgo |
| --- | --- |
| ¿Usó mocks donde bastaba un stub? | **No.** Usó un doble falso (`PagoFalso`) con los dos atributos que lee la calculadora, sin `Mock` ni verificación de llamadas. Es la elección correcta: la calculadora no tiene colaboradores externos. |
| ¿Las aserciones son significativas? | **Sí.** Las 23 pruebas comparan fechas y estados exactos y cubren los bordes (vence hoy, venció ayer, febrero bisiesto, pagos anulados). Con el import corregido detectaron los 4 mutantes, igual que la suite del proyecto. |
| ¿Alucinó algo? | **Sí: un módulo.** Importó `dominio.calculos`, que no existe; tal cual, la suite no arranca (`ModuleNotFoundError`). Lo advirtió («ajustar a la ruta real»), pero el nombre se lo inventó. |
| Riesgo que no vio | `PagoFalso` no es el `Pago` real. Si `Pago.esta_vigente()` cambia, estas pruebas siguen en verde. Por eso la suite del proyecto prueba la calculadora con el `Pago` real del dominio. Su observación sobre la duración 0 es cierta para la función aislada, pero `Plan` ya rechaza duraciones ≤ 0 al crearse. |

**Corrección.** No se agregaron al repositorio: la suite del proyecto ya cubre las mismas reglas con el `Pago` real y también mató los 4 mutantes. Queda como evidencia de que esta IA genera buenas pruebas de una función pura, si se le corrige el import.
