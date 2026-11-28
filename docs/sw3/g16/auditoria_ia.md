# Auditoría de IA · Guía 16 (matriz de responsabilidades)

**Herramienta.** Claude (Anthropic), 27/11/2026. El servicio se describió sin URL, sin nombres de cuentas y sin secretos.

**Prompt.** «Haz una matriz de responsabilidades, equipo o proveedor, para una aplicación Django empaquetada en una imagen Docker y desplegada como Web Service en Render, con una base Render Postgres del plan gratuito. Filas: aplicación, runtime, sistema operativo, datos, respaldos, acceso y actualizaciones.»

**Fragmento relevante de la salida.**

| Actividad | Responsable |
| --- | --- |
| Aplicación | Equipo |
| Runtime (Python) | **Proveedor: Render mantiene actualizado el entorno de ejecución** |
| Sistema operativo | Proveedor |
| Datos | Compartida |
| Respaldos | **Proveedor: Render hace copias diarias automáticas de la base** |
| Acceso | **Proveedor: Render gestiona la autenticación y los permisos** |
| Actualizaciones | Proveedor |

## Criterio de verificación

Cada fila se contrasta con la documentación de Render consultada el 27/11/2026 y con lo que FitManage tiene en el repositorio. Una atribución es correcta solo si las dos fuentes coinciden.

| Fila | Qué dice la fuente | Veredicto |
| --- | --- | --- |
| Respaldos | `render.com/docs/free`: «Free Render Postgres databases don't support any form of backups». `render.com/docs/postgresql-backups`: «Render does not provide recovery capabilities for databases on the Free compute plan». | **Incorrecta.** En el plan Free el respaldo es del equipo. |
| Runtime | El servicio se despliega desde una imagen propia (`deploy.yml`, `imgURL=sha-<commit>`). El `Dockerfile` fija `python:3.12-slim-trixie@sha256:b18b…`. Render no toca lo que hay dentro de la imagen. | **Incorrecta para este despliegue.** Sería del proveedor con un runtime nativo de Render, pero FitManage no lo usa. |
| Sistema operativo | El host y el núcleo son de Render. Los paquetes Debian de la imagen los actualiza el equipo cuando cambia el digest, y Trivy los revisa en CI. | Parcial: es compartida. |
| Acceso | Render autentica a quien entra a su panel. Los usuarios del gimnasio, sus roles y los tokens son de la aplicación (ADR N.° 06), y los secretos los custodia el equipo. | Parcial: es compartida. |
| Actualizaciones | Las de la plataforma son de Render. Las de la aplicación y sus dependencias son del equipo (Dependabot y `resumen-dependabot.yml`). | Parcial: es compartida. |

## Corrección y prueba de la tarea del equipo

La matriz corregida es la de `clasificacion_y_responsabilidades.md`. La fila que más importa es la de respaldos. Si el equipo hubiera creído a la IA, el 2/12/2026, cuando vence la base gratuita, no habría ninguna copia de los datos.

**Tarea del equipo probada.** Respaldar y restaurar la base. `despliegue_reproducible.sh` hace un `pg_dump`, borra la base, la restaura y verifica que los datos y las reglas sigan ahí. La salida está en `despliegue_reproducible_salida.txt`.

**Segunda comprobación.** Que el runtime es del equipo se ve en el repositorio. Dependabot y Trivy trabajan sobre el `Dockerfile`, y el digest de la imagen base cambia solo con un commit nuestro.

**Limitación.** La misma sesión generó la salida y la auditó. Las dos atribuciones que se corrigieron se apoyan en citas textuales del proveedor y en archivos del repositorio, no en la opinión de quien revisa. Las páginas de Render pueden cambiar: se consultaron el 27/11/2026.
