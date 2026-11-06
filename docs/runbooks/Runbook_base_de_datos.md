# Runbook · La base de datos no responde

| | |
| --- | --- |
| **Alertas que lo abren** | `PresupuestoQuemaRapida` o `PresupuestoQuemaLenta` (SLO de disponibilidad, ADR N.° 14), `ErroresDelServidor` en Grafana Cloud, o una llamada del gimnasio: «FitManage no carga». |
| **Síntoma** | La consulta de estado responde 500, y `/api/v1/salud` responde **503 `SERVICIO_NO_DISPONIBLE`**. |
| **Responsable** | Juan Sebastián Cárdenas Acevedo, la única persona del equipo. No hay guardia 24/7: las alertas llegan por correo y se atienden en el horario del gimnasio (5:00 a. m. a 10:00 p. m.). |
| **Contacto del gimnasio** | El administrador de la sede, por WhatsApp. |
| **Probado** | En el simulacro de la Guía 14 (workflow `Simulacro de incidente`), con los mismos comandos de este documento. |

Este runbook no pide herramientas de pago ni personas que no existen. Todo se hace con un navegador, el panel de Render y, si hay una terminal a mano, `curl`.

## Paso 1 · Avisar y activar el plan B en recepción (2 minutos)

Antes de diagnosticar, avisar al gimnasio para que no se quede esperando. Mensaje para el administrador:

> Hola. FitManage tiene una falla y la estoy revisando. Mientras tanto, en recepción anoten en una hoja el nombre, el documento y la hora de cada persona que entre, y pidan el comprobante de pago a quien diga que pagó hoy. Les escribo apenas esté arreglado.

La hoja se guarda en recepción y se destruye después de registrar las entradas en FitManage (paso 6): tiene datos personales (Ley 1581).

## Paso 2 · Diagnosticar sin tocar nada (1 minuto)

Con una terminal (Linux, macOS o Git Bash):

```bash
docs/runbooks/diagnostico_bd.sh produccion
```

Sin el repositorio a mano, desde PowerShell:

```powershell
curl.exe -s -w "`nHTTP %{http_code}`n" https://fitmanage-svol.onrender.com/api/v1/salud
```

O abrir `https://fitmanage-svol.onrender.com/api/v1/salud` en el celular. Qué significa la respuesta:

| Respuesta | Qué pasa | Ir a |
| --- | --- | --- |
| **200** con `"estado": "ok"` | La app y la base están bien. La alerta viene de otra cosa (una ruta concreta, la latencia). | Tablero de Grafana, panel «Tasa de peticiones por código». |
| **503** con `SERVICIO_NO_DISPONIBLE` | La app está viva pero no llega a PostgreSQL. | Paso 3 |
| **Sin respuesta** o la página «Service waking up» que dura más de 2 minutos | La app misma está caída. | Paso 3, caso D |

En el entorno de compose, el mismo script con `compose` muestra además el estado del contenedor, `pg_isready` y el último error de la app.

## Paso 3 · Encontrar la causa en el panel de Render (5 minutos)

Abrir el panel de Render → la base de datos de FitManage. Revisar en este orden:

**A. La base gratuita venció.** Las bases gratuitas de Render vencen **30 días después de crearse** y quedan inaccesibles. Hay **14 días de gracia** para pasarla a un plan pago; después Render la borra con todos sus datos, y el plan gratuito no tiene copias de seguridad. Si el panel muestra la base vencida:
- Dentro de los 14 días: pasarla al plan pago más barato (US$6 al mes, 256 MB). Los datos se recuperan.
- Después de los 14 días: los datos se perdieron. Crear una base nueva, poner su *Internal Database URL* en `DATABASE_URL` del servicio y desplegar (las migraciones corren solas con `arrancar.sh`). Avisar al gimnasio que hay que volver a cargar socios y pagos.

**B. Render reinició la base o le está haciendo mantenimiento.** Render advierte que puede hacerlo en cualquier momento. Revisar también `https://status.render.com`. No hay que hacer nada en la app: Django vuelve a conectarse solo en la siguiente petición (`CONN_HEALTH_CHECKS`), como se comprobó en el simulacro. Esperar y volver al paso 2 cada 5 minutos.

**C. El disco se llenó.** La base gratuita tiene 1 GB fijo. Si el panel muestra el almacenamiento lleno, la única salida rápida es pasarla a un plan pago con más espacio.

**D. La app no arranca.** En el servicio web → *Events*: si el último despliegue falló, la versión anterior sigue en línea. Si la app no responde después de un despliegue que sí salió, usar *Manual Deploy* → *Deploy latest reference*: la *Image URL* es `ghcr.io/gamero29/fitmanage:estable`, la última imagen que pasó el healthcheck. Si fue un cambio de variables, revisar en *Environment* que `DATABASE_URL` sea la *Internal Database URL* de la base.

## Paso 4 · Recuperar

Según el caso del paso 3. En compose, el equivalente de «la base vuelve» es:

```bash
docker compose start db
docker compose exec -T db pg_isready -U fitmanage     # debe decir «accepting connections»
```

## Paso 5 · Verificar antes de dar por cerrado

1. `/api/v1/salud` responde **200 tres veces seguidas**, con un minuto entre cada una.
2. En Grafana, «Errores 5xx» vuelve a 0 % y la alerta pasa a *Normal* (la rápida se apaga unos 5 minutos después, porque mira los últimos 5 minutos).
3. Desde recepción, consultar el estado de un socio conocido.

## Paso 6 · Cerrar

1. Avisar al gimnasio: «FitManage ya funciona. Gracias por la paciencia. Me pueden mandar la foto de la hoja de entradas y la registro.»
2. Registrar en FitManage los pagos anotados en la hoja y pedir que la destruyan.
3. En las 48 horas siguientes, escribir el postmortem con la plantilla de [`docs/postmortems/`](../postmortems/): línea de tiempo, impacto en el presupuesto de error y acciones, sin buscar culpables.
4. Si el presupuesto de error de los últimos 14 días quedó en 0 % o menos, aplicar la política del ADR N.° 14: no se despliegan funciones nuevas hasta que vuelva a ser positivo.

## Qué NO hacer

- No borrar ni recrear la base mientras exista la opción de pasarla a un plan pago: se pierden los datos.
- No reiniciar el servicio web «por si acaso» en el caso B: no cambia nada y se pierde el registro de lo que pasó en los logs del proceso.
- No pegar la `DATABASE_URL`, los tokens ni las claves en un chat o en un ticket.
