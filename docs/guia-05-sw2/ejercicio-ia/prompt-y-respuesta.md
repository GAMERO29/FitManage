# Ejercicio 4 · Microservicios en la nube para un negocio pequeño

**Herramienta:** Claude (Anthropic), sesión nueva. **Fecha:** 30/10/2026.

## Prompt

> Diseña una arquitectura de microservicios distribuidos en la nube para un gimnasio pequeño que tiene unas 300 transacciones al día (consultas de socios y pagos de membresía).

## Respuesta de la IA (sin modificar)

> Para un gimnasio con bajo volumen, una arquitectura **serverless de microservicios en AWS** es ideal porque solo pagas por lo que usas:
>
> 1. **Servicios:** `usuarios-service`, `socios-service`, `membresias-service`, `pagos-service` y `notificaciones-service`, cada uno como un conjunto de funciones **AWS Lambda**.
> 2. **Entrada:** **Amazon API Gateway** con autenticación mediante **Amazon Cognito**.
> 3. **Datos:** cada servicio con su propia base de datos **Amazon RDS for PostgreSQL** (patrón *database per service*), en subredes privadas de una VPC.
> 4. **Comunicación:** eventos asíncronos con **Amazon EventBridge** (`PagoRegistrado`, `MembresiaRenovada`) para mantener la consistencia eventual entre servicios.
> 5. **Frontend:** aplicación React alojada en **S3 + CloudFront**.
> 6. **Notificaciones:** **Amazon SNS** para enviar SMS de recordatorio de vencimiento.
>
> **Costos:** gracias al modelo de pago por uso y a la capa gratuita, con 300 transacciones diarias el costo mensual sería prácticamente nulo, de unos pocos dólares.
>
> **Ventajas:** escalado automático, alta disponibilidad gestionada por AWS sin servidores que mantener, y cada servicio se puede desplegar de forma independiente.

## Auditoría

Ver el Ejercicio 4 de la guía resuelta y `docs/guia-05-sw2/costos.md`.
