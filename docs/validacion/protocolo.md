# Protocolo de validación de FitManage

Guía II-06 · 10/11/2026 · Autor: Juan Sebastián Cárdenas Acevedo.

**Estado:** protocolo ensayado en seco por el autor. **No se ha hecho ninguna sesión con participantes del perfil.** La tabla de observaciones está vacía a propósito y no se llenará con datos supuestos.

## 1. Preguntas

- **V1 (uso):** ¿una recepcionista que nunca vio FitManage sabe, sin ayuda, si un socio puede pasar y cobra un plan dejando bien la membresía?
- **V2 (comprensión):** ¿entiende qué hacer cuando el sistema no responde, en vez de repetir la operación?
- **V3 (corrección):** ¿corrige un cobro equivocado dejando el estado final correcto y el motivo?
- **V4 (administración):** ¿el administrador encuentra quién deshizo un cobro y entiende qué pasa con un cambio de precio?

Decisión que cambiaría: si V1 o V3 fallan sin ayuda en más de una persona, no se inicia el piloto hasta corregir interfaz o material (ver `docs/piloto/plan_piloto.md`).

## 2. Perfiles y selección

| Perfil | Quién sirve | Quién no sirve |
| --- | --- | --- |
| Recepcionista | Persona que atiende o ha atendido la recepción de un gimnasio, o un mostrador con cobro (tienda, papelería). Que use el celular a diario. | Estudiantes de sistemas, el autor, quien ya vio FitManage. |
| Administrador | Dueño o encargado que responde por el dinero de un negocio pequeño. | Un administrador técnico de servidores. |
| Responsable técnico | Lo cubre el autor con el runbook. No se valida con usuarios: se ensaya (II-05). | — |

Meta de muestra: 3 a 5 recepcionistas y 1 a 2 administradores. Con esa muestra solo se detectan problemas graves; no se calcula ningún porcentaje del mercado.

## 3. Versión, entorno y datos

- Versión: el commit de `main` que integra este protocolo, corriendo **en local**: con Docker Compose (README, sección «Con Docker») o, como en el laboratorio de II-05, gunicorn con un PostgreSQL 16 local. **Nunca en producción:** la auditoría es imborrable y T4 detiene la base a propósito.
- Antes de **cada** participante: base nueva (`docker compose down -v` y `up`) y `node ensayo_en_seco.js http://127.0.0.1:8000 --solo-preparar`, para que la socia ficticia *Ana Prueba Demo* (CC 1090000011) tenga un mes pagado. Sin esto, la persona 2 vería los pagos de la persona 1.
- Cuenta de práctica: *Laura Demo* (recepcionista, la crea el script) o el administrador local. El script supone que el administrador local es `admin@demo.local` con la clave de demostración `clave-de-demo-local`, creado con `python manage.py preparar_gimnasio` y las variables `FITMANAGE_ADMIN_NOMBRE`, `FITMANAGE_ADMIN_CORREO` y `FITMANAGE_ADMIN_CLAVE`; solo sirve en local. Ninguna cuenta real.

## 4. Consentimiento (se lee antes de empezar)

> Gracias por ayudarme. Estoy probando un programa para la recepción de un gimnasio; lo que se evalúa es el programa, no usted. Si algo no le sale, es un problema del programa y eso es justo lo que necesito encontrar. Todo lo que verá son datos inventados. Voy a tomar notas de lo que hace y de lo que dice, sin su nombre: usted será «R1» o «A1». No voy a grabar video ni audio a menos que usted me diga que sí ahora. Puede parar o retirarse en cualquier momento sin dar explicaciones, y si se retira borro sus notas. ¿Está de acuerdo? ¿Acepta que grabe la pantalla, sin su cara ni su voz?

Se anota «acepta notas: sí/no» y «acepta grabación de pantalla: sí/no». Si dice que no a la grabación, no se graba.

## 5. Tareas (consignas neutrales)

Se leen tal cual. Si la persona pregunta «¿dónde le doy?», se responde «¿dónde cree que sería?». Revisión mecánica de pistas: `revisar_consignas.py` (primera salida con 3 coincidencias en `consignas_v1_salida.txt`; corregida en `consignas_v2_salida.txt`).

| Tarea | Perfil | Consigna | Completa correctamente si… |
| --- | --- | --- | --- |
| T1 | Recepcionista | Llega Ana, una socia, con su cédula 1090000011 y quiere pasar a entrenar. Averigüe si puede hacerlo y hasta qué día. | Dice que puede pasar y la fecha de vencimiento que muestra la pantalla. |
| T2 | Recepcionista | Ana quiere pagar otro mes. Le muestra en el celular una transferencia por Nequi con el número M123456. Deje el pago listo para que el sistema lo reconozca. | Queda un pago Mensual vigente, Nequi, referencia M123456, y la persona dice hasta cuándo queda. |
| T3 | Recepcionista | Cinco minutos después Ana vuelve: quería quince días, no un mes, y usted ya le cobró el mes. Deje las cosas como deben quedar. | El Mensual M123456 queda anulado con un motivo y hay un Quincenal vigente. Las dos rutas (cambiar plan, o anular y cobrar de nuevo) valen. |
| T4 | Recepcionista | Mientras atiende a la persona que sigue en la fila, la pantalla muestra algo distinto de lo habitual. Cuente qué hace con la persona que espera. *(El facilitador detiene la base local: `docker compose stop db`, o `docs/capacitacion/caida.js` en el laboratorio de II-05.)* | Anota en papel o avisa, y no repite la operación más de una vez. |
| T5 | Recepcionista | No recuerda cómo se corrige un cobro equivocado. Encuentre cómo hacerlo con el material que tiene a mano, sin preguntarme. | Llega a la sección 3 de la guía rápida impresa. |
| A1 | Administrador | El dueño cree que hoy alguien deshizo un cobro en el mostrador. Averigüe quién fue, a qué hora y qué razón dio. | Dice el nombre, la hora y el motivo (en Auditoría o en el historial del socio). |
| A2 | Administrador | Desde el lunes, el plan de un mes cuesta 80.000. Haga el cambio y explique qué pasa con quienes ya pagaron. | Cambia el precio y explica que lo ya pagado no cambia. |

**Categorías de resultado** (acordadas antes de observar): *completa sin ayuda*; *completa con ayuda* (se anota qué se le dijo); *no completa* (se rinde o el estado final es incorrecto); *no intenta*. Un resultado con ayuda nunca se cuenta como autónomo. Si el facilitador da la respuesta, se puede seguir explorando, pero la tarea queda «con ayuda».

## 6. Registro

| Participante | Tarea y versión | Resultado y ayuda | Observación (conducta, no opinión) y evidencia |
| --- | --- | --- | --- |
| — | — | — | Sin sesiones a la fecha. |

Se anota conducta observable: «se detuvo en el mensaje y preguntó si debía repetir», nunca «no sabe usar tecnología». Las frases de cortesía («está muy bonito») se anotan aparte y no cuentan como resultado.

## 7. Ensayo previo del protocolo

No hubo ensayo con un compañero. Lo que sí se hizo, y sus límites:

1. **Revisión mecánica de consignas** (`revisar_consignas.py`): comparó las 7 consignas con 94 textos de la interfaz. La primera versión tenía 3 coincidencias: «entrar» (botón **Entrar** del ingreso), «siguiente» (botón **Siguiente** de la auditoría) y «días». Cambié T1 a «pasar a entrenar» y T4 a «la persona que sigue en la fila». «Días» se quedó: es como habla la socia, no el nombre de un botón.
2. **Ensayo en seco** (`ensayo_en_seco.js`): ejecuté T1, T2, T3 (ruta de cambiar plan), A1 y A2 en la versión local y comprobé con la API que el criterio de éxito se puede observar: 5 de 5. T4 se ensayó con `docs/capacitacion/caida.js` y T5 con la guía rápida.
3. **Correcciones al protocolo que salieron del ensayo:** reiniciar la base entre participantes; aceptar las dos rutas de T3 (al principio solo había pensado en anular); prohibir producción porque T4 detiene la base y la auditoría no se borra.
4. **Pregunta que el ensayo destapó y que solo una persona del oficio puede responder:** en T3, Ana pagó 75.000 por Nequi y el plan correcto vale 45.000. FitManage no registra devoluciones. Hay que preguntar cómo se maneja hoy esa diferencia.

**Límite:** el autor conoce la interfaz, así que el ensayo prueba que las tareas son posibles y observables, no que sean comprensibles. Eso solo lo dice una sesión con el perfil.
