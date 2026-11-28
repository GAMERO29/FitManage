# Clasificación de escenarios y matriz de responsabilidades · Guía 16

Definiciones de NIST SP 800-145, sección 2: *Service Models* y *Deployment Models*. Precios consultados el 27/11/2026.

## 1. Cuatro escenarios en los dos ejes

**Criterio del eje de despliegue:** para quién se aprovisiona la infraestructura. Es pública si es de uso abierto, privada si es exclusiva de una organización, comunitaria si la comparte un grupo de organizaciones con intereses comunes, e híbrida si se componen dos o más infraestructuras distintas unidas por una tecnología que permite mover datos y aplicaciones.

**Criterio del eje de servicio:** hasta dónde llega el control del equipo. En IaaS controla el sistema operativo y lo que corre encima. En PaaS despliega su aplicación sobre un entorno administrado. En SaaS solo usa una aplicación ajena y configura lo que ella permite.

| # | Escenario | Despliegue | Servicio | Por qué |
| --- | --- | --- | --- | --- |
| E1 | FitManage hoy: la imagen `sha-<commit>` corre como Web Service de Render con Render Postgres | Pública | PaaS | Render es de uso abierto. El equipo entrega una imagen y variables; no ve el sistema operativo del host ni el servidor de la base. |
| E2 | Una nube que comparten varias universidades públicas de la región por convenio, con las mismas políticas de datos, y que le entrega al equipo una VM Ubuntu (escenario supuesto, no hay convenio real) | Comunitaria | IaaS | La usa un grupo de organizaciones con requisitos comunes, no el público. El equipo instala y parcha el sistema invitado, PostgreSQL y la aplicación. |
| E3 | El gimnasio contrata un software de agenda y membresías listo para usar (AgendaPro, plan Básico, COP 99.000 al mes) | Pública | SaaS | El gimnasio solo configura su cuenta y sus servicios. No despliega código ni elige base de datos. |
| E4 | FitManage en Render envía métricas y trazas por OTLP a Grafana Cloud (ADR N.° 13) | Dos nubes públicas integradas, **no híbrida** | PaaS + SaaS | Hay dos infraestructuras distintas conectadas, pero lo que las une es un envío de telemetría. No hay portabilidad de datos ni de la aplicación entre ellas. Para llamarla híbrida haría falta, por ejemplo, poder levantar la misma imagen en la nube comunitaria de E2 y mover la base con el mismo procedimiento, y demostrarlo. |

## 2. Matriz de responsabilidades por opción

E = equipo FitManage (una persona). P = proveedor. C = compartida, con el detalle de qué hace cada uno.

| Actividad | IaaS: VM DigitalOcean de 1 GiB (US$6 al mes) | PaaS: Render, Web Service y Postgres | SaaS: AgendaPro Básico |
| --- | --- | --- | --- |
| **Aplicación** (código, reglas RN-01 a RN-07, versiones) | E | E. La imagen la construye CI y la despliega `deploy.yml`. | P. El gimnasio acepta el flujo del producto; RN-03 y la auditoría de solo inserción no se pueden exigir. |
| **Runtime** (Python 3.12, gunicorn, dependencias) | E | **E.** Va dentro de la imagen: `FROM python:3.12-slim-trixie@sha256:…` en el `Dockerfile`, con Dependabot y Trivy en CI. Render no lo actualiza. | P |
| **Sistema operativo** | E. Sistema invitado: parches, firewall, SSH, TLS con certbot. P: hipervisor y hardware. | C. P: el host, el núcleo y el sistema del servidor de la base. E: los paquetes Debian de la imagen. | P |
| **Datos** (contenido, esquema, migraciones, Ley 1581) | E. PostgreSQL instalado por el equipo. | C. P opera el servidor PostgreSQL. E responde por el esquema (migraciones en `arrancar.sh`), el contenido y el tratamiento de datos personales. | C. P los guarda. El gimnasio sigue siendo responsable del tratamiento ante el titular, y depende de lo que el contrato permita exportar. |
| **Respaldos** | C. P ofrece copias de la VM entera (20 % semanal o 30 % diario del costo de la VM). E respalda la base con `pg_dump` y prueba la restauración. | **Plan Free: E**, porque Render dice «Free Render Postgres databases don't support any form of backups». **Plan pago: C.** P hace PITR de 3 días (Hobby). E guarda un `pg_dump` semanal fuera de Render y prueba la restauración (`despliegue_reproducible.sh`). | P, según el contrato. E solo puede pedir exportaciones. |
| **Acceso** | E: usuarios del sistema, llaves SSH y cuentas de la aplicación. P: cuenta del proveedor y red. | C. P: TLS del dominio `onrender.com`, red y panel. E: la cuenta del panel, los secretos (`RENDER_DEPLOY_HOOK`, `JWT_CLAVE`) y los roles de la aplicación (JWT, ADR N.° 06). | C. P: autenticación. E: alta y baja de usuarios del gimnasio. |

**Lectura.** Las tres opciones cubren la necesidad operativa, que es atender la recepción con el estado de cada socio en menos de 2 s, pero no dejan lo mismo en manos del equipo. La IaaS es la más barata en efectivo y la que más trabajo deja, en una organización con una sola persona técnica y sin guardia nocturna. La SaaS es la que menos trabajo deja y la más cara. Además obliga a aceptar un flujo que no conoce las reglas propias de FitManage. El PaaS deja al equipo lo que de todos modos tiene que saber hacer: la aplicación, sus datos y su respaldo.
