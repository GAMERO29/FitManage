# language: es
# Escenarios obligatorios de aceptación del DDS (sección 15.1), automatizados contra la API real.
# Cada «Dado» arranca de los datos de demostración en una base efímera.
Característica: Membresías y cobros en la recepción del gimnasio
  Como recepcionista o administrador
  quiero que FitManage aplique las reglas del negocio sin que yo calcule nada
  para atender la fila rápido y sin errores de plata

  Escenario: PA-01 Registrar un socio con un documento que ya existe
    Dado que la recepcionista inició sesión
    Cuando registra un socio con el documento CC 1090123456
    Entonces la respuesta es 409 con el código DOCUMENTO_DUPLICADO
    Y sigue existiendo un solo socio con ese documento

  Escenario: PA-02 Un plan trimestral pagado el 01/03/2026 vence el 29/05/2026
    Dado que hoy es 2026-03-01 a las 10:00 en Colombia
    Y que la recepcionista inició sesión
    Cuando registra un pago Trimestral en efectivo para PPT 25789456
    Entonces el pago inicia el 2026-03-01 y vence el 2026-05-29

  Escenario: PA-03 Renovar el mismo día del vencimiento no hace perder días
    Dado que hoy es 2026-10-21 a las 18:00 en Colombia
    Y que la recepcionista inició sesión
    Cuando registra un pago Mensual en efectivo para CC 1090123456
    Entonces el pago inicia el 2026-10-22 y vence el 2026-11-20

  Escenario: PA-05 A las 7:30 p. m. un socio que vence hoy sigue activo
    Dado que hoy es 2026-10-21 a las 19:30 en Colombia
    Y que la recepcionista inició sesión
    Cuando consulta el estado de CC 1090123456
    Entonces el estado es ACTIVO con 1 día restante

  Escenario: PA-07 La recepcionista no puede anular ni ver ingresos
    Dado que la recepcionista inició sesión
    Cuando intenta anular el último pago de CC 1093445566
    Entonces la respuesta es 403 con el código SIN_PERMISO
    Cuando intenta abrir el reporte de ingresos de octubre
    Entonces la respuesta es 403 con el código SIN_PERMISO

  Escenario: PA-08 Anular el último pago recalcula el estado
    Dado que el administrador inició sesión
    Cuando anula el último pago de CC 1093445566 porque "Se registró el plan equivocado"
    Entonces el pago queda ANULADO con el motivo guardado
    Y el estado de CC 1093445566 es SIN_MEMBRESIA

  Escenario: PA-09 La referencia de un pago anulado se puede volver a usar
    Dado que el administrador inició sesión
    Y que anuló el último pago de CC 1093445566 porque "Comprobante mal digitado"
    Cuando registra un pago Mensual por NEQUI con referencia M123456 para CC 1093445566
    Entonces la respuesta es 201

  Escenario: PA-10 Cinco intentos fallidos bloquean la cuenta 15 minutos
    Cuando Laura escribe mal su contraseña 5 veces
    Entonces la respuesta es 423 con el código CUENTA_BLOQUEADA
    Y ni con la contraseña correcta puede entrar hasta 15 minutos después

  Escenario: PA-11 Un doble clic en «Confirmar pago» registra un solo pago
    Dado que la recepcionista inició sesión
    Cuando envía dos veces el mismo pago Mensual en efectivo para CC 1093445566
    Entonces las dos respuestas son iguales
    Y CC 1093445566 tiene 2 pagos guardados
