# Auditoría de IA · Guía 12 (recomendación antes de ver resultados)

**Prompt (antes de correr el experimento).** «Para la anulación de pagos de un sistema de
gimnasio en Django (anular el último pago, anular por id y anular dentro de un cambio de plan),
¿conviene Transaction Script o Domain Model? Recomienda uno y justifica.»

**Fragmento relevante.** «Para un sistema CRUD pequeño como un gimnasio, Domain Model es
sobreingeniería. **Transaction Script siempre es la mejor opción en aplicaciones pequeñas**: menos
clases, menos capas y más velocidad de desarrollo. Domain Model solo se justifica en dominios
complejos como banca o seguros.»

## Comparación con lo observado

| Argumento de la IA | Observación del experimento | Veredicto |
| --- | --- | --- |
| «Menos clases» | Cierto: TS son 81 líneas en un archivo. | Correcto, pero no decide nada. |
| «Más velocidad de desarrollo» | La primera versión sí fue más rápida. El cambio CR-02 costó 3 lugares en TS y 1 en DM. | Parcial: más rápido al escribir, más lento al cambiar. |
| «Siempre es la mejor opción en aplicaciones pequeñas» | La aplicación es pequeña, pero este flujo tiene tres entradas que comparten cuatro reglas. Lo que pesa es cuántas operaciones comparten invariantes, no el tamaño del sistema. | **Generalización incorrecta.** |
| «Solo en banca o seguros» | La complejidad que importa aquí es pequeña pero real: la recepcionista corrige su día, el cambio de plan no tiene ese límite y siempre se anula el último. | Incorrecto para este caso. |

**Corrección.** La recomendación queda limitada al caso investigado. Transaction Script conviene
en flujos de una sola entrada que no comparten reglas (como los reportes, que ya son scripts de
consulta). Domain Model conviene para la anulación, porque tres entradas comparten las mismas
reglas. Así lo registra el ADR N.° 21 con su condición de revisión.

**Limitación.** La misma sesión hizo la recomendación y la auditó. El experimento tiene un solo
flujo y la medida de esfuerzo es en líneas y lugares, no en horas.
