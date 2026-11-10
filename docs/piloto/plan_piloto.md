# Plan de piloto, soporte y decisión

Guía II-06 · 10/11/2026 · Responsable del producto, del soporte y de la decisión técnica: Juan Sebastián Cárdenas Acevedo (trabaja solo). La aceptación académica la da el docente; la decisión de usarlo en un gimnasio, su dueño.

## Decisión

**No inicio todavía un piloto externo.** Lo hecho hasta hoy es un ensayo local con datos ficticios. Para pasar a un piloto con un gimnasio real faltan cuatro condiciones, en este orden:

1. **H1:** base de datos paga con copias de seguridad. La gratuita vence cerca del 2/12/2026 y no tiene respaldos.
2. **DT-10:** aviso de privacidad y autorización de tratamiento de datos aprobados (Ley 1581 de 2012). Sin eso no se puede registrar un socio real.
3. **DEF-03:** quien tenga las credenciales de la base puede vaciar la auditoría con `TRUNCATE`. Hay que bloquearlo o separar las credenciales antes de que el rastro importe.
4. **Validación:** al menos tres sesiones con recepcionistas del perfil (`docs/validacion/protocolo.md`) sin bloqueos en T1 a T3.

DEF-05 (un 403 no registra quién lo intentó) también debe corregirse antes del piloto, pero no lo bloquea: no hay riesgo de perder datos.

## Piloto propuesto, cuando se cumplan las condiciones

| Campo | Definición |
| --- | --- |
| Propósito | Saber si la recepción de un gimnasio pequeño puede reemplazar el cuaderno por FitManage para consultar y cobrar, sin perder control del dinero. |
| Población | Un gimnasio, su recepción (1 a 3 personas) y su dueño como administrador. |
| Capacidades habilitadas | Consulta de estado, registro de socios y pagos, corrección (anular o cambiar plan), vencimientos, reportes, planes, personal y auditoría. |
| Excluido | Correo saliente (DT-26), funcionamiento sin conexión (QA-02, hito H4), devoluciones de dinero, más de un gimnasio, entrenadores. |
| Duración | 4 semanas, la ventana que el hito H4 del roadmap necesita para medir el presupuesto de error. Cierra antes si se cumple una condición de parada. |
| Datos | Socios reales del gimnasio, solo con la autorización firmada (DT-10). El cuaderno sigue en paralelo la primera semana. |
| Entorno | Render, con la base paga (H1), y la versión identificada por `/api/v1/salud`. |
| Recuperación | Runbook de II-05; restauración ensayada en un destino separado; señal de coherencia de la auditoría cada semana. |

## Condiciones de parada

Se detiene el piloto, se vuelve al cuaderno y se avisa al dueño el mismo día si pasa cualquiera de estas:

- La consulta de coherencia (`docs/guia-ii05/coherencia_auditoria.sql`) devuelve un pago sin su evento.
- Un pago cambia o desaparece sin quedar en la auditoría.
- El estado de un socio sale equivocado frente al cuaderno.
- Alguien hace una operación que su rol no permite.
- Se agota el presupuesto de error del ADR N.° 14 (99,5 % en 14 días) en la primera semana.
- Se carga un dato personal sin la autorización firmada.

## Criterios de salida, definidos antes de mirar los datos

Los umbrales los propongo yo y debe revisarlos el docente antes del piloto. Ninguna dimensión compensa a otra.

| Dimensión | Pregunta | Criterio propuesto | Evidencia |
| --- | --- | --- | --- |
| Utilidad | ¿Resuelve la consulta en la fila? | El dueño decide seguir usándolo sin el cuaderno después de la semana 1. | Decisión del dueño, por escrito. |
| Uso | ¿Se entiende con la guía rápida? | Ningún cobro mal hecho que la recepcionista no haya sabido corregir sola. | Auditoría (anulaciones y cambios de plan con su motivo) y registro de soporte. |
| Calidad | ¿Se mantienen los controles críticos? | Cero filas en la consulta de coherencia; cero defectos críticos abiertos. | Consulta semanal y lista de defectos. |
| Operación | ¿Se sostiene y se recupera? | SLO de disponibilidad del ADR N.° 14 cumplido en las ventanas de 14 días. | Grafana Cloud. |
| Sostenibilidad | ¿Lo puedo atender? | Horas reales de soporte y mantenimiento ≤ las de la oferta (5 h al mes). | Registro de soporte con horas. |

Resultado posible: ampliar, corregir y repetir, seguir evaluando o detener. «Aceptado» solo se escribe si el dueño lo decide y lo firma.

## Acuerdo de soporte

| Campo | Acuerdo |
| --- | --- |
| Canal | Un solo canal escrito que se acuerda con el dueño al iniciar el piloto (correo o chat del responsable). No se publica aquí. Las llamadas no se atienden como canal de soporte, porque no dejan registro. |
| Horario propuesto | Lunes a viernes, de 6:00 p. m. a 9:00 p. m., y sábados, de 9:00 a. m. a 12:00 m. Es una propuesta: lo confirmo antes del piloto según mi horario de estudio. Fuera de ese horario no hay atención; el plan B es el cuaderno. |
| Tipos de solicitud | **Bloqueo** (no se puede consultar ni cobrar); **error** (algo sale mal, pero hay forma de seguir); **duda**; **cambio** (algo nuevo). |
| Primera respuesta (objetivo, no garantía) | Bloqueo: 2 horas dentro del horario. Error: 1 día hábil. Duda y cambio: 2 días hábiles. |
| Resolución | No prometo un tiempo de resolución. Respondo qué pasó, qué hacer mientras tanto y cuándo espero tener la corrección. Los cambios entran al backlog con su evidencia; no se hacen durante el piloto, salvo para corregir un defecto. |
| Información que pido | Qué estaba haciendo, hora, mensaje exacto, y la versión que muestra `/api/v1/salud` si la sabe. Nunca contraseñas ni fotos de documentos de socios. |
| Escalamiento | No hay un segundo nivel: soy la única persona. Si la caída es de Render, consulto su página de estado y lo informo. Si no puedo resolver un bloqueo en un día, recomiendo volver al cuaderno hasta la corrección. |
| Registro | Cada solicitud con fecha, versión, tipo, efecto en la tarea, horas dedicadas y cierre. |

## Backlog después del piloto

Se ordena por evidencia y riesgo, no por catálogo: primero DEF-03, DEF-05 y DT-10; después lo que muestre la validación (H-04 ayuda en línea, H-05 devoluciones); después H4 (recepción sin conexión). Las funciones nuevas que pida el gimnasio entran con la necesidad observada, el costo en horas y el riesgo.
