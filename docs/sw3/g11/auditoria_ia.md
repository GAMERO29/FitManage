# Auditoría de IA · Guía 11 (modelo de dominio)

**Prompt.** «Propón el modelo de dominio de un sistema de membresías para un gimnasio pequeño:
agregados, entidades, objetos de valor e invariantes.» Anonimizado: sin el nombre del gimnasio
ni datos de socios.

**Fragmento relevante de la salida.**

```text
Agregado Gimnasio (raíz): contiene Socios, Planes, Pagos y Membresias.
Invariantes:
  - Un socio solo puede tener una membresía activa y un pago vigente a la vez.
  - Un pago vence 30 días después de la fecha de pago.
  - Un plan con socios activos no se puede modificar.
Membresia (entidad): estado, fecha_inicio, fecha_fin.
```

## Verificación contra requisitos y observaciones

| Propuesta | Contraste | Resultado |
| --- | --- | --- |
| Agregado `Gimnasio` con todo adentro | El límite debe ser el menor que proteja las invariantes (Fowler, *DDD Aggregate*) | **Sobredimensionado.** Registrar un pago bloquearía a todo el gimnasio; con dos recepcionistas en hora pico, una esperaría a la otra. FitManage bloquea solo la fila del socio. |
| «Un solo pago vigente a la vez» | RN-04 y CA-06: renovar antes de vencer crea un segundo pago vigente | **Regla inventada y falsa.** `test_el_siguiente_periodo_no_se_solapa_con_los_vigentes` trabaja justo con dos pagos vigentes. |
| «Vence 30 días después» | RN-03: inicio + duración − 1, según el plan | **Inventada.** Además tiene el mismo error de un día que se vio en la Guía 08. |
| «Un plan con socios activos no se modifica» | RF-02 y RN-09: se edita el precio; los pagos guardan copia del valor (RN-08) | **Inventada.** Bloquearía subir precios. |
| `Membresia` como entidad con estado | RN-05: el estado no se almacena | **Contradice el requisito.** |

## Corrección

El modelo vigente está en [`glosario_y_reglas.md`](glosario_y_reglas.md) y [`agregado.png`](agregado.png):
un agregado por socio, las invariantes I-1 a I-6 con su origen, y la referencia de comprobante
(I-5) fuera del agregado, resuelta por la base. Cada invariante del agregado tiene una prueba en
[`pruebas_agregado.txt`](pruebas_agregado.txt).

**Limitación.** La misma sesión generó y auditó el modelo.
