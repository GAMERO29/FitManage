# Ejercicio 4 · Arquitectura recomendada por una IA sin contexto

**Herramienta:** Claude (Anthropic), sesión de chat nueva. **Fecha:** 30/10/2026.
**Contexto entregado:** a propósito, ninguno sobre el tamaño del negocio, el presupuesto ni el equipo, como pide la guía.

## Prompt

> Recomiéndame una arquitectura de software para FitManage, una aplicación para gestionar gimnasios: socios, membresías, pagos y control de acceso en recepción.

## Respuesta de la IA (sin modificar)

> Para una plataforma de gestión de gimnasios escalable y preparada para el crecimiento, recomiendo una **arquitectura de microservicios** desplegada en la nube:
>
> 1. **Microservicios independientes:** servicio de usuarios y autenticación, servicio de socios, servicio de membresías, servicio de pagos y servicio de notificaciones. Cada uno con su propia base de datos (PostgreSQL para socios y pagos, MongoDB para notificaciones), siguiendo el patrón *database per service*.
> 2. **API Gateway** (Kong o AWS API Gateway) como punto único de entrada, con limitación de peticiones y autenticación centralizada.
> 3. **Mensajería asíncrona con Apache Kafka** para comunicar eventos entre servicios (por ejemplo, `PagoRegistrado` → actualizar membresía → enviar notificación).
> 4. **Orquestación con Kubernetes** (Amazon EKS) con autoescalado horizontal y despliegue en varias zonas de disponibilidad para alta disponibilidad.
> 5. **Frontend:** aplicación web en React y aplicación móvil en React Native para socios y personal.
> 6. **Caché con Redis** para acelerar la consulta del estado de las membresías.
> 7. **Observabilidad:** Prometheus y Grafana para métricas, y la pila ELK para registros.
> 8. **Autenticación** con OAuth 2.0 y OpenID Connect mediante Auth0 o Amazon Cognito.
>
> Esta arquitectura permite escalar cada servicio de forma independiente, desplegar sin tiempo de inactividad y agregar nuevas funcionalidades sin afectar al resto del sistema.

## Auditoría y corrección

Ver el Ejercicio 4 de la guía resuelta y el ADR N.° 03 (`docs/adr/ADR-003-unidad-de-despliegue.md`).
