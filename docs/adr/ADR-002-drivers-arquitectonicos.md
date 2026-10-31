# ADR N.° 02 · Drivers arquitectónicos priorizados de FitManage

| Campo | Contenido |
| --- | --- |
| Estado | Aceptado (30/10/2026) |
| Contexto | El ERS ya traía RNF con métricas (RNF-01 a RNF-07), pero ninguno estaba escrito como escenario completo y varios atributos que terminaron en deuda nunca se definieron: la concurrencia de pagos (DT-01), la corrección de las fechas con un servidor en UTC (DT-07), la facilidad para probar (DT-02, DT-09) y el control de acceso en el servidor (DT-05). El MVP lo desarrolla una sola persona, con costo cero de infraestructura (R-01) y en una recepción con internet inestable (R-03). |
| Decisión | Se priorizan tres drivers, en este orden: 1) fiabilidad de las reglas de membresía y de los pagos (QA-03, QA-05); 2) disponibilidad y rapidez de la consulta en recepción (QA-02, QA-01); 3) seguridad del acceso y de los datos personales (QA-04). Cada decisión de arquitectura de las próximas guías debe decir qué escenario favorece y cuál sacrifica. Los escenarios que se pueden automatizar se vuelven pruebas del flujo `Calidad`; QA-03 ya lo es. |
| Consecuencias (positivas y negativas) | A favor: las decisiones se discuten contra medidas concretas, y la deuda que viene de atributos sin definir deja de aparecer en silencio. En contra: el desempeño con muchos usuarios y la escalabilidad quedan en segundo plano, lo cual es razonable para un gimnasio con 1 a 3 equipos en recepción pero tendría que revisarse si FitManage atiende varias sedes. QA-01, QA-02 y QA-04 no se pueden verificar hasta construir la interfaz web. |
