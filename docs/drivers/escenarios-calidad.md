# Drivers arquitectónicos y escenarios de calidad (FPI-18)

Plantilla del SEI: fuente, estímulo, artefacto, entorno, respuesta y medida. Atributos según ISO/IEC 25010:2023. Cada escenario indica cómo se verifica y qué ítem de deuda o requisito lo origina.

| ID | Atributo (ISO/IEC 25010) | Fuente | Estímulo | Artefacto | Entorno | Respuesta | Medida | Origen | Verificación |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| QA-01 | Eficiencia de desempeño (comportamiento temporal) | Recepcionista | Consulta el estado de un socio por número de documento | Consulta de estado (`recepcion`, `CalculadoraMembresia`, `PagoRepositorio`) | Hora pico (5:30 a 7:30 p. m.), 10 usuarios simultáneos, conexión de 10 Mbps, base de prueba con 2.000 socios y 20.000 pagos | Muestra Activo, Vencido o Sin membresía con la fecha de vencimiento | El 95 % de las consultas responde en menos de 2 s y ninguna termina en error durante una prueba de carga de 10 minutos | RNF-01 | Prueba de carga cuando exista la vista web (semanas 5 y 6) |
| QA-02 | Fiabilidad (disponibilidad) | Proveedor de internet del gimnasio | Se cae la conexión | Consulta en recepción (Service Worker y caché del navegador) | Hora pico; la última sincronización fue hace 5 minutos o menos | Sigue respondiendo en solo lectura con un aviso visible, bloquea el registro de pagos y muestra un aviso naranja si los datos tienen más de 12 horas | El 100 % de los socios en caché se consulta en menos de 1 s, el aviso aparece en 3 s o menos y no se registra ningún pago sin conexión | RNF-06, R-03 | Prueba en navegador con la red desactivada (semana 6) |
| QA-03 | Fiabilidad (madurez y corrección temporal) | Reloj del servidor, configurado en UTC | Una recepcionista consulta a las 7:30 p. m. a un socio que vence ese día | `RelojBogota` y `CalculadoraMembresia` | Servidor en la nube en UTC (ya son las 00:30 del día siguiente) | Muestra al socio como Activo | El 100 % de los casos límite de fecha pasa en cada ejecución del flujo `Calidad` | DT-07, CP-04c | `tests/test_reloj.py` (automática, ya vigente) |
| QA-04 | Seguridad (confidencialidad y autenticidad) | Recepcionista con sesión válida | Abre `/reportes/ingresos/` o envía directamente la anulación de un pago | Autorización por rol en la capa de aplicación (`@requiere_rol`) | Operación normal en producción con HTTPS | Rechaza la acción y registra el intento en la auditoría | El 100 % de las rutas de administrador responde 403 a la recepcionista y ninguna respuesta incluye datos de ingresos | DT-05, RNF-05, CP-09a | Prueba automática que recorre todas las rutas protegidas (semana 5) |
| QA-05 | Seguridad (integridad) | Dos recepcionistas | Registran al mismo tiempo dos pagos con la misma referencia de Nequi | `PagoRepositorio` sobre PostgreSQL 16 | Hora pico, dos PC conectados a la misma base de datos | Guarda uno de los pagos y rechaza el otro con «Comprobante duplicado» | Cero referencias duplicadas en 100 repeticiones de la prueba concurrente | DT-01, RN-06, CP-03c | Prueba de integración con PostgreSQL en el flujo `Calidad` (semana 4) |
| QA-06 | Mantenibilidad (modificabilidad) | Dueño del gimnasio | Pide aceptar pagos con tarjeta débito | `MedioPago` y el registro de pagos | Desarrollo normal, con la suite de pruebas y el flujo `Calidad` | El nuevo medio se agrega sin modificar los servicios ni la calculadora | Máximo 2 archivos de producción cambiados, 0 pruebas existentes rotas y cobertura de 95 % o más | Diseño OCP del DAD | Experimento del 30/10/2026: 1 archivo y 1 línea de producción, 70 de 70 pruebas aprobadas |

## Drivers priorizados

1. **Fiabilidad de las reglas de membresía y de los pagos** (QA-03 y QA-05).
2. **Disponibilidad y rapidez de la consulta en recepción** (QA-02 y QA-01).
3. **Seguridad del acceso y de los datos personales** (QA-04 y Ley 1581 de 2012).

La justificación está en el ADR N.° 02 (`docs/adr/ADR-002-drivers-arquitectonicos.md`).

## Trade-offs aceptados

| Atributos en conflicto | Decisión | Motivo |
| --- | --- | --- |
| Disponibilidad de la consulta frente a exactitud de los datos | Sin conexión solo se consulta, con datos de hasta 5 minutos y aviso visible; los pagos se bloquean | Internet inestable en recepción (R-03); dejar entrar a alguien que venció hace minutos cuesta menos que detener la fila |
| Seguridad frente a usabilidad y desempeño | bcrypt y bloqueo tras 5 intentos solo al iniciar sesión; la sesión dura el turno de 8 horas en el PC de recepción | La consulta, que se repite cientos de veces por noche, no paga el costo del hash |
| Costo frente a disponibilidad del servidor | Se acepta la capa gratuita del PaaS para el piloto, aunque se suspenda por inactividad; la caché del navegador cubre la consulta | R-01 (cero costo) y la condición del DAD de presupuestar un plan básico antes de la puesta en marcha |
| Mantenibilidad frente a complejidad inicial | Interfaces solo en las fronteras de entrada y salida (puertos) | Criterio del DAD: evitar sobreingeniería con un solo desarrollador |
