# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Recepcionista** (persona de ejemplo: Laura). Atiende el mostrador de un gimnasio pequeño en Cúcuta. Su tarea más frecuente es decir en segundos si un socio puede entrar, con fila en la puerta y a veces sin internet. También registra socios y pagos y abre recordatorios por WhatsApp.
- **Administrador o dueño** (persona de ejemplo: Carlos). Revisa ingresos por medio de pago, anula pagos con motivo, administra planes y cuentas del personal. Entra pocas veces por semana.

## Product Purpose

FitManage reemplaza el cuaderno y la hoja de cálculo con los que una MiPyme de gimnasio controla membresías y pagos. El éxito es que la recepción responda «activo / vencido / sin membresía» sin dudar, que ningún pago se duplique ni se pierda y que el dueño sepa cuánto entró y por qué medio.

## Positioning

Está hecho para la realidad de un gimnasio de barrio en Colombia: pagos por Nequi, Daviplata, transferencia y efectivo con control de comprobantes duplicados; recordatorios por enlace de WhatsApp sin costo; consulta de estado que sigue funcionando con la caché del navegador cuando se cae el internet; y fechas calculadas en hora de Colombia con renovación anticipada que no hace perder días al socio.

## Operating Context

- Mostrador de recepción, computador de escritorio o portátil; el celular del personal como respaldo (vista móvil sin conexión).
- Internet inestable (R-03); la consulta debe funcionar con datos en caché y decir cuándo se sincronizó.
- El socio muestra en su celular el comprobante de Nequi o Daviplata y la recepcionista digita la referencia.
- Documentos de identidad colombianos y de extranjeros: CC, CE, PPT, pasaporte.

## Capabilities and Constraints

- Roles: recepcionista y administrador. Reportes, historial con anulación, planes y personal son solo del administrador; el servidor responde 403 y lo registra en auditoría.
- Planes: Diario (1 día), Quincenal (15), Mensual (30), Trimestral (90). Vencimiento = inicio + duración − 1 día (RN-03). Renovación anticipada inicia el día siguiente al vencimiento actual (RN-04).
- Un pago no se borra: se anula con motivo, usuario y fecha; solo el último pago vigente (RN-07).
- Autorización de tratamiento de datos obligatoria al registrar un socio (Ley 1581 de 2012).
- Bloqueo de cuenta tras 5 intentos fallidos durante 15 minutos.
- No hay un gimnasio aliado específico: el producto está pensado para MiPymes de gimnasio en general.

## Brand Commitments

- Nombre: FitManage.
- Logo elegido: «anillo de vigencia», una mancuerna dentro de un anillo. Su morado oscuro (#23005A) es el color de marca y se conserva.

## Evidence on Hand

- Prototipo navegable en `prototipo/FitManage_Prototipo.html` con datos de demostración (Ana Pérez, Jorge Rincón, María Fernanda Gil, etc.). Los nombres, precios y totales son ficticios y se marcan como demostración.
- No hay clientes, testimonios ni cifras de uso reales: no se deben inventar.

## Product Principles

1. La respuesta de recepción gana: el estado del socio se lee de un vistazo y desde lejos.
2. El dinero no se adivina: el sistema calcula fechas y montos y muestra por qué.
3. Nada se borra en silencio: cada anulación deja rastro.
4. Funciona en el gimnasio real: con internet que se cae y medios de pago locales.

## Accessibility & Inclusion

- Estado nunca solo por color: siempre texto y forma además del color.
- Objetivos táctiles de al menos 44 px; foco visible; textos en español de Colombia.
