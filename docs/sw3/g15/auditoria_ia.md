# Auditoría de IA · Guía 15 (beneficios de la nube)

**Herramienta.** Claude (Anthropic), 27/11/2026. Sin datos de socios, sin URL de producción y sin credenciales.

**Prompt.** «Compara los beneficios de alojar en la nube frente a un servidor local una aplicación web de recepción para un gimnasio pequeño en Colombia (Django y PostgreSQL, una o dos recepcionistas).»

**Fragmento relevante de la salida.**

> Migrar a la nube le permitirá al gimnasio:
> 1. **Reducir los costos de TI entre un 30 % y un 50 %**, porque elimina la compra y el mantenimiento de servidores propios.
> 2. **Escalar automáticamente** en temporadas de alta demanda, como enero, sin intervención del equipo.
> 3. **Disponibilidad del 99,99 %** gracias a la infraestructura redundante del proveedor.
> 4. **Respaldos automáticos diarios**, de modo que nunca se pierdan los datos de los socios.

## Criterio de verificación

Cada afirmación tiene que poder comprobarse con el caso de FitManage. Eso pide un supuesto explícito (carga, periodo y plan del proveedor), una fuente con fecha o una medición propia. Si no hay nada de eso, la afirmación se reescribe como hipótesis con la forma de probarla.

| Afirmación | Qué se encontró | Veredicto |
| --- | --- | --- |
| Ahorro del 30 % al 50 % | No dice frente a qué ni con qué carga. Con los supuestos de `evaluacion_alojamiento.md`, la alternativa local con un mini PC propio cuesta unos COP 49.000 al mes y la nube paga mínima en Render unos COP 44.000 al mes. La diferencia en efectivo es de un 10 %, no del 30 % al 50 %, y depende de cuántos meses dure el equipo local. | Falsa para este caso. Recalculada. |
| Escalado automático | En Render, el autoescalado «requires a Pro workspace plan or higher» (US$25 al mes más el cómputo), y una instancia gratuita no escala («1 (scaling unavailable)»). Además, la medición no muestra necesidad: con 10 usuarios simultáneos, unas 5 veces la carga nominal, el p95 local fue de 11,9 ms. | Engañosa: el plan actual no la tiene y la carga no la pide. |
| Disponibilidad del 99,99 % | No cita ningún acuerdo de servicio. El plan que usa FitManage es gratuito: el servicio web se duerme tras 15 minutos sin tráfico y tarda «about one minute» en despertar. El ADR N.° 14 fijó un SLO propio del 99,5 % medido en Grafana, no una promesa del proveedor. | Sin sustento. Reformulada como hipótesis. |
| Respaldos automáticos diarios | La documentación de Render dice: «Free Render Postgres databases don't support any form of backups». En los planes pagos hay recuperación a un punto en el tiempo (PITR) de 3 días en el plan Hobby. | Falsa para la base actual. Corregida. |

## Corrección

1. **Costo recalculado** con la misma carga, unidades y periodo para las dos alternativas: COP 49.000 en local y COP 44.000 en Render, por mes. El detalle y las fuentes están en `evaluacion_alojamiento.md`. El beneficio que sí se puede defender no es el ahorro en efectivo. Es que el equipo no administra el sistema operativo ni el hardware y que el respaldo sale del proveedor, siempre que la base esté en un plan pago.
2. **Elasticidad como hipótesis verificable.** «Si la demanda de enero llega al doble de la nominal, una sola instancia de 512 MB mantiene el p95 de la consulta de estado por debajo de 300 ms sin escalar.» Se prueba con k6 en el laboratorio a 2 y 10 usuarios simultáneos (hecho: 11,8 ms y 11,9 ms) y se confirma en producción con el histograma de Grafana en la primera quincena de enero.
3. **Disponibilidad como hipótesis verificable.** «Con la base en el plan pago, FitManage cumple el SLO del 99,5 % en una ventana de 14 días.» Se mide con el SLI del ADR N.° 14: consultas que no terminan en 5xx dividido entre todas las consultas.
4. **Respaldo.** Mientras la base siga en el plan gratuito, el único respaldo posible es el `pg_dump` que haga el equipo. La prueba de restauración está en la Guía 16 (`docs/sw3/g16/`).

**Limitación.** La misma sesión que redactó la salida de la IA la auditó. Por eso cada veredicto se apoya en una cita de la documentación del proveedor o en una medición guardada en esta carpeta, no en el criterio de quien revisa.
