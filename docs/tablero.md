# Cómo se trabaja FitManage: tablero y acuerdo de terminado

Guía II-02 (9/11/2026). Trabajo solo, así que este documento es el acuerdo conmigo mismo y lo que el docente puede revisar.

## Tablero

El tablero son las etiquetas de los issues del repositorio. Un ítem es un issue; su PR lo cierra al integrarse.

| Columna | Etiqueta | Límite | Entra cuando… |
| --- | --- | --- | --- |
| Opciones | `tablero:opciones` | sin límite | alguien propone algo y no lo descarto |
| Preparado | `tablero:preparado` | 4 | cumple la política de entrada |
| Construcción | `tablero:construcción` | **1** | empiezo a escribir código o pruebas |
| Verificación | `tablero:verificación` | **1** | abro el PR |
| Terminado | issue cerrado por un PR integrado | - | cumple el acuerdo de terminado |

**Límite global: 2 ítems iniciados** (construcción + verificación). Los PR de Dependabot cuentan dentro de verificación.

## Políticas

- **Entrada a Preparado:** la regla está escrita y confirmada (o marcada como supuesto), la aceptación se puede probar, las dependencias están dichas y la estimación es de 6 horas o menos. Si es más, se parte.
- **Salida a Terminado:** el PR pasa los nueve checks; hay prueba del caso válido, de un permiso negado y de un error; el contrato y la documentación afectada están al día; no hay secretos ni datos reales. Si el ítem escribe en `pagos` o en `auditoria`, también una prueba en PostgreSQL de dos operaciones al mismo tiempo (lección de D-01 y D-02).
- **Bloqueo:** se pone la etiqueta `bloqueado` sin sacar el ítem de su columna, y se comenta la causa, desde cuándo, quién puede resolverlo y el siguiente paso. El ítem sigue contando en el WIP.
- **Urgencia:** solo un defecto en producción o una vulnerabilidad alta o crítica pasa por encima del límite. Se anota el motivo en el issue.
- **Dependabot:** al empezar cada sesión de trabajo reviso los PR de Dependabot abiertos. Si llevan más de 48 horas, se tratan como bloqueados.

## Revisión

No hay un segundo desarrollador. Revisan el pipeline (nueve checks obligatorios en `main`) y yo con la lista del acuerdo; el docente revisa cada entrega. Lo que no tuvo revisión independiente se dice en la ficha de la guía.
