# Roadmap técnico de FitManage · noviembre de 2026 a mayo de 2027

Guía 15 (FPI-31, ADR N.° 15). Cada hito tiene un **disparador**: el hecho que obliga a empezarlo. Una fecha sola no basta. Las horas son estimaciones de una sola persona, con el ritmo de este semestre como referencia. La política del presupuesto de error (ADR N.° 14) manda sobre este orden: si el presupuesto de 14 días llega a 0 %, se detienen los hitos perfectivos y se trabaja en confiabilidad.

| Hito | Tipo de mantenimiento | Disparador | Fecha límite | Esfuerzo | Deuda que paga |
| --- | --- | --- | --- | --- | --- |
| **H0. Destrabar las actualizaciones** | Preventivo | Ya ocurrió: 7 PR de Dependabot bloqueados | 13/11/2026 (**cumplido el 6/11/2026**) | 1 h | DT-17 |
| **H1. Infraestructura que no se borre** | Adaptativo y preventivo | La base gratuita vence cerca del **2/12/2026** y Render la borra 14 días después | 1/12/2026 | 4 h | DT-18, DT-20 |
| **H2. Listo para datos reales** | Correctivo de cumplimiento y perfectivo | El gimnasio acepta un piloto con socios reales | Antes del primer socio real (meta: 31/1/2027) | 32 h | DT-10, DT-13, DT-14, DT-15, DT-23 |
| **H3. Revisión de las excepciones de seguridad** | Preventivo | Las 12 excepciones de `.trivyignore` vencen el **1/2/2027** y la puerta vuelve a fallar sola | 25/1/2027 | 3 h | DT-19 |
| **H4. Recepción sin conexión** | Perfectivo | Cuatro semanas de piloto sin agotar el presupuesto de error | Marzo de 2027 | 20 h | QA-02 pendiente |
| **H5. Django 6.2 LTS** | Adaptativo | Sale Django 6.2 LTS (abril de 2027) y su primer parche, 6.2.1 | 31/5/2027 | 12 h | DT-21, DT-22 |

## H0 · Destrabar las actualizaciones (1 h)

- Crear `SONAR_TOKEN` en *Settings → Secrets and variables → Dependabot*. GitHub no les pasa los secretos de Actions a los PR de Dependabot.
- Volver a correr los PR abiertos. Fusionar los que pasen los nueve checks y cerrar Django 6.1 (#20) y `openapi-spec-validator` 0.9 (#21), que Dependabot ya ignora.

**Cumplido el 6/11/2026:** secreto creado y PR #17, #18, #22, #31, #32 y #33 fusionados.

**Justificación de negocio:** mientras los PR se acumulan, los parches de seguridad no llegan, y el escaneo semanal de la FPI-28 pierde sentido.

## H1 · Infraestructura que no se borre (4 h)

- Pasar la base de Render al plan de US$6 al mes (las bases pagas tienen copias de seguridad; las gratuitas no), o exportarla con `pg_dump` por la *External Database URL* y crear otra gratuita. La decisión es del gimnasio: son US$72 al año.
- Medir de nuevo el SLO dos semanas después del cambio.
- Pasar a Grafana Cloud las alertas del SLO del recorrido de recepción, como en `slo.yml` (DT-20).

**Justificación de negocio:** sin este hito, el 16/12/2026 se pierden todos los socios y pagos cargados. Es el único hito con fecha impuesta desde afuera.

## H2 · Listo para datos reales (32 h)

- **DT-10:** redactar con el dueño del gimnasio el aviso de privacidad y la autorización de tratamiento (Ley 1581), versionarlos en `docs/legal/` y guardar con cada socio la versión que aceptó.
- **DT-14:** tabla `auditoria` de solo inserción, escrita en la misma transacción de cada pago, anulación y bloqueo de cuenta; completar PA-08.
- **DT-13:** límite de 60 intentos por minuto en `/auth/token` y `/salud`, con su prueba del 429 que ya documenta el contrato.
- **DT-15:** decidir con el dueño del requisito entre configurar bcrypt o actualizar el RNF-04, y medir el inicio de sesión con k6.
- **DT-26:** restablecer contraseñas con un servidor de correo y la página que recibe el enlace. La gestión de planes y de cuentas (DT-24) ya está desde el 7/11/2026 (ADR N.° 17).
- **DT-23:** la clave de idempotencia pasa a ser por usuario y se rechaza la misma clave con otro cuerpo. Primero el contrato (`openapi.yaml`, con el código de error nuevo en formato problem+json), después el código.

**Justificación de negocio:** sin aviso de privacidad, la autorización de los socios no es válida; sin auditoría, una anulación de pago no deja rastro. Las dos cosas las puede pedir la SIC.

## H3 · Revisión de las excepciones de seguridad (3 h)

- Para cada CVE de `.trivyignore`: si Debian ya publicó el parche, actualizar la imagen base y borrar la excepción; si no, revisar que la razón siga siendo cierta y renovar la fecha.

**Justificación de negocio:** si no se hace, el 1/2/2027 la puerta bloquea todos los despliegues, incluidos los arreglos urgentes.

## H4 · Recepción sin conexión (20 h)

- Terminar la vista móvil con el Service Worker de QA-02: guardar en caché los estados del día (`/api/v1/estados?cambiadosDesde=`) y consultarlos aunque la API no responda.

**Justificación de negocio:** en los dos simulacros de la FPI-30, recepción tuvo que pasar a la hoja de papel durante 30 minutos. Con la caché, la consulta sigue funcionando durante una caída de la base, sin pagar una réplica de US$80 al mes.

## H5 · Django 6.2 LTS (12 h)

- Migrar de 5.2 LTS a 6.2 LTS, con la suite completa, el contrato y el k6 de QA-01 como red de seguridad.
- Revisar si `openapi-core` ya admite `openapi-spec-validator` 0.9 y quitar las dos reglas `ignore` de Dependabot.

**Justificación de negocio:** 5.2 recibe parches de seguridad hasta abril de 2028. Migrar en mayo de 2027 deja casi un año de margen para hacerlo sin prisa.

## Lo que se decidió no hacer

- **DT-04 y DT-06 (prototipo):** se convive con ellos. El prototipo no entra a la imagen ni al despliegue.
- **DT-12 (`Pago` guarda entidades completas):** se convive. Solo se paga si se separa un contexto del monolito (ADR N.° 05).
- **Réplica de la base o un SLO mayor que 99,5 %:** cuesta US$80 al mes y el gimnasio tiene un plan B (ADR N.° 14). H4 da casi el mismo beneficio a recepción.
