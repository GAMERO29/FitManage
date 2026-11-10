# Expediente de entrega de FitManage

Índice para continuar el proyecto sin depender del autor. Guía II-06 · 10/11/2026 · Juan Sebastián Cárdenas Acevedo.

**Versión de referencia:** el commit de `main` que integra este índice (v1.1.0 más las correcciones de mensajes H-01 a H-03). Producción corre lo que diga `https://fitmanage-svol.onrender.com/api/v1/salud`. El esquema es la migración `0003_auditoria_y_coherencia_de_anulacion` y el contrato, `docs/api/openapi.yaml` 1.7.0.

## Los ocho formatos

No tengo las plantillas institucionales de los formatos. La numeración sale de lo que piden las guías II-01 a II-06; el formato 1 no lo nombra ninguna de ellas, así que lo asumo como problema y viabilidad.

| Formato | Pregunta | Dónde está, en su versión vigente | Guía que lo actualizó |
| --- | --- | --- | --- |
| 1 · Problema y viabilidad | ¿Para quién y para qué sirve? ¿Se puede sostener? | `docs/Dossier_Final.md` (secciones 1 y 2), `docs/drivers/escenarios-calidad.md` | I-02, I-03 |
| 2 · Análisis y modelos | ¿Cómo circula la información y qué reglas la gobiernan? | `docs/guia-ii01/` (diagramas `.mmd` y `.png`, recorrido R1 a R14) | II-01 |
| 3 · Decisiones de arquitectura | ¿Por qué está construido así? | `docs/adr/` (ADR N.° 1 a 19), `docs/arquitectura/` | I-04, II-03 |
| 4 · Método y gestión | ¿Cómo se trabaja y qué capacidad hay? | `docs/tablero.md`, `docs/guia-ii02/`, `docs/roadmap.md` | II-02 |
| 5 · Construcción | ¿Qué incremento se hizo y cómo? | PR #63 a #66, migración 0003, `docs/guia-ii03/` | I-05, II-03 |
| 6 · Calidad | ¿Qué se probó, qué falló y qué falta? | `docs/pruebas/estrategia.md`, `docs/guia-ii04/`, `docs/deuda-tecnica.md` | I-06, II-04 |
| 7 · Operación, uso y adopción | ¿Cómo se instala, se observa, se recupera, se aprende y se pide ayuda? | `docs/runbooks/`, `docs/releases/v1.1.0.md`, `docs/guia-ii05/`, `docs/capacitacion/guia_rapida.md`, `docs/validacion/`, `docs/piloto/plan_piloto.md` | II-05, II-06 |
| 8 · Evidencia individual | ¿Qué hizo el estudiante y qué hizo la IA? | Las fichas II-01 a II-06 (fuera del repositorio), `docs/guia-16-sw2/bitacora-ia.md`, el historial de PR | Todas |

**Documentos que no actualicé en estas guías:** el ERS, el DDS y el DAD (`ERS_FitManage.docx`, `DDS_FitManage.docx`, `DAD_FitManage.docx`, en el proyecto de claude.ai) y el prototipo `prototipo/FitManage_Prototipo.html`. No reflejan los ADR N.° 18 y 19 ni la auditoría. Ante una diferencia, mandan los ADR y el código.

## Código, artefacto e instrucciones

| Pieza | Dónde |
| --- | --- |
| Código | https://github.com/GAMERO29/FitManage, rama `main` (solo se integra por PR con los 12 checks en verde) |
| Imagen | `ghcr.io/gamero29/fitmanage:sha-<commit>`, la publica el pipeline |
| Instalar en local | `README.md`, sección «Con Docker» |
| Desplegar y revertir | `docs/runbooks/Runbook_entrega.md` |
| Incidente de base de datos | `docs/runbooks/Runbook_base_de_datos.md` y el postmortem del 6/11/2026 |
| Contrato y errores | `docs/api/openapi.yaml`, `docs/api/errores.md` |
| Usar el producto | `docs/capacitacion/guia_rapida.md` |
| Validar con usuarios | `docs/validacion/protocolo.md` |
| Piloto y soporte | `docs/piloto/plan_piloto.md` |

## Accesos

Los secretos (Deploy Hook de Render, claves de la base, `DJANGO_SECRET_KEY`, `JWT_CLAVE`, token de Grafana) están solo en el panel de Render y en el environment `produccion` de GitHub. No van en este expediente. Una persona que continúe el proyecto los recibe del dueño del repositorio, que la agrega como colaboradora en GitHub y en Render; después se rotan.

## Limitaciones conocidas, en un solo lugar

- Ningún usuario del perfil ha usado el sistema. La validación está pendiente (`docs/validacion/protocolo.md`).
- Sin respaldos en producción hasta el hito H1; la base gratuita vence cerca del 2/12/2026.
- DEF-03 y DEF-05 abiertos; DT-10 sin resolver: no se cargan datos reales.
- Sin funcionamiento sin conexión (QA-02, H4) ni correo saliente (DT-26).
- Un gimnasio por instalación: no hay separación entre gimnasios en el modelo de datos.
