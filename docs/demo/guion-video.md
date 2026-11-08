# Guion del video demo (máximo 5 minutos)

Guía 16 de Software II (FPI-32, sección B) y Guía 16 de Software I (FPI-16, sección C). Un solo video sirve para las dos. Todo lo que se muestra existe en el repositorio o en producción.

## Antes de grabar

1. **Grabador.** En Windows 11, la Herramienta Recortes (modo video, con micrófono). En cualquier sistema, OBS Studio. Graba la pantalla completa a 1080p, porque vas a cambiar de pestaña.
2. **Micrófono.** Haz una prueba de 10 segundos y escúchala. Mejor audífonos con micrófono que el del portátil.
3. **Pantalla limpia.** Activa «No molestar», cierra WhatsApp y el correo, oculta la barra de marcadores (Ctrl+Shift+B) y pon el zoom del navegador en 125 %.
4. **Pestañas abiertas, en este orden:**
   1. `https://fitmanage-svol.onrender.com/`. Ábrela 2 minutos antes: el plan gratuito se duerme y el primer arranque tarda.
   2. PR #42 del repositorio, pestaña **Checks** (es el PR que nació del tablero de Grafana).
   3. Settings → Rules → Rulesets → «Puerta de calidad de main».
   4. Releases → **v1.0.0**.
   5. Grafana Cloud: el tablero de producción en «Last 24 hours».
   6. `docs/postmortems/2026-11-06-base-de-datos-30-minutos.md`.
   7. `docs/guia-16-sw2/bitacora-ia.md`.
   8. `docs/deuda-tecnica.md` y `docs/roadmap.md`.
5. **Datos inventados.** Usa un número nuevo en cada intento, porque en el intento anterior ya quedó registrado: 1090000011, luego 1090000012, y así. Nombre «Ana Prueba Demo», celular 3001234567, comprobante M123456. No consultes ningún documento real (DT-10).
6. **Lo que no debe salir en cámara.** Las variables de Render, Settings → Secrets del repositorio, las claves de Grafana y la lista de contraseñas guardadas del navegador.
7. **Ensayo.** Haz una pasada completa con cronómetro antes de grabar la buena.

## Guion

El texto entre comillas es para decirlo con tus palabras; no hace falta leerlo literal.

### 0:00–0:25 · El problema

**En pantalla:** el inicio de sesión de FitManage en producción.

> «Soy Juan Sebastián Cárdenas y este es FitManage, el proyecto integrador de Ingeniería de Software I y II. El problema salió de observar la recepción de un gimnasio de barrio: en hora pico, la recepcionista no sabe si quien llega pagó, y la fila crece. FitManage responde eso por documento, en segundos. Todo lo que van a ver está en producción.»

### 0:25–1:45 · El flujo crítico en vivo

| Haces | Dices |
| --- | --- |
| Inicias sesión. | «Entro como administrador. El token dura 15 minutos y se renueva con una cookie que JavaScript no puede leer: es el ADR 06.» |
| Consultas CC 1090000011. | «Consulto una cédula que no existe. El sistema me dice que no está registrada y me ofrece registrarla.» |
| Registrar socio: Ana Prueba Demo, 3001234567, marcas la autorización. | «Uso datos inventados. Fíjense en el aviso: el texto legal de privacidad de la Ley 1581 todavía no está aprobado, así que solo se cargan datos de prueba. Es la deuda DT-10.» |
| Aparece «Sin membresía». Registrar pago: Mensual, Nequi, M123456. **Doble clic** en «Confirmar pago». | «Ahora no tiene membresía. Registro un pago mensual por Nequi. Yo no escribo el valor ni las fechas: los calcula el servidor con el plan vigente. Y pulso confirmar dos veces a propósito, porque en recepción pasa cuando el internet está lento. Cada pago lleva una clave de idempotencia y queda uno solo.» |
| Aparece «Puede entrar», 30 días. | «Puede entrar, con 30 días. Ese es el flujo crítico: los casos de uso 02, 03 y 04.» |

### 1:45–2:10 · En el celular

**En pantalla:** en la misma pestaña, F12 → Ctrl+Shift+M → Pixel 7, y vuelves a consultar el documento.

> «Es la misma pantalla en tamaño de celular, porque el personal muchas veces consulta desde el suyo. El documento sale enmascarado: la consulta no muestra el número completo.»

Cierra las herramientas con F12 antes de seguir.

### 2:10–3:00 · La puerta de calidad (ADR 09 y ADR 12)

**En pantalla:** PR #42 → Checks; luego la regla de `main`; luego el release v1.0.0.

> «Nada entra a `main` sin un PR que pase nueve checks obligatorios: estilo, pruebas con cobertura mínima de 95 % (el proyecto está en 99 %), SonarCloud, el contrato de la API, la imagen probada contra PostgreSQL, Semgrep, el escaneo de dependencias y de la imagen, y la búsqueda de secretos. La regla de `main` no permite push directo ni reescribir la historia. Un hallazgo crítico o alto de seguridad detiene el merge, y cada excepción tiene justificación y fecha de vencimiento: eso es el ADR 12. Dependabot está activo y hoy reporta cero alertas. Esta es la versión final, la v1.0.0.»

### 3:00–3:55 · Producción y decisiones (ADR 05 y ADR 14)

**En pantalla:** el tablero de Grafana; luego el postmortem.

> «Este es el tablero de producción de las últimas 24 horas: p95 de 108 milisegundos y 0 % de errores. Además encontró un defecto que ninguna prueba había visto: peticiones HEAD a la página principal respondían 405. Se corrigió en el PR que acabo de mostrar.
>
> ¿Por qué no microservicios? Con 10 recepcionistas a la vez, un solo proceso responde con p95 de 13,5 milisegundos, y el límite es de 2 segundos. Distribuir costaría unos 94 dólares al mes, y en los simulacros lo que se cayó fue la base de datos: más servicios no arreglan eso. Ese es el ADR 05.
>
> El SLO es de 99,5 % en 14 días. Un apagón de la base de 30 minutos consumió el 30 % del presupuesto de error, y la alerta avisó a los 2 minutos. Con 99,9 %, ese solo incidente lo habría agotado. Ese es el ADR 14.»

### 3:55–4:25 · Auditoría ética de IA

**En pantalla:** `bitacora-ia.md`, la tabla de totales.

> «Usé IA durante las 31 fichas y quedó auditado: 16 alucinaciones comprobadas, 30 dependencias rechazadas, 7 propuestas con secretos en claro que no entraron al código y 2 fugas de datos personales evitadas. Ningún documento de socio aparece en logs, métricas ni trazas: hay un workflow que falla si encuentra uno.»

### 4:25–5:00 · Lo que falta

**En pantalla:** `deuda-tecnica.md` y `roadmap.md`.

> «Lo pendiente, sin rodeos: la base gratuita de Render vence cerca del 2 de diciembre; falta aprobar el aviso de privacidad antes del primer socio real, y no hay pantalla para crear planes ni personal. Lo más importante: ningún usuario real ha usado el sistema todavía. La verificación es fuerte; validar con una recepcionista real es el primer pendiente del roadmap. Gracias.»

## Después de grabar

1. Revisa que dure 5:00 o menos y que se oiga bien.
2. Súbelo a YouTube como **No listado** (o a Google Drive con «Cualquier persona con el enlace»). Abre el enlace en una ventana de incógnito para comprobar que se ve.
3. Ese enlace va en la FPI-32 (sección B), en la FPI-16 (sección C) y en el README.
