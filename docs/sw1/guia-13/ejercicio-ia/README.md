# Guía 13 (FPI-13) · Una IA resuelve un conflicto de mezcla

- **Conflicto:** real, en una copia aparte (`../conflicto/`). La rama `mensual-mes-calendario` cambió la duración del plan Mensual a 31 días; la rama `precio-mensual-2027`, el precio a 80.000.
- **IA:** Claude Haiku. Prompt y respuesta sin editar en esta carpeta.

| Pregunta de la guía | Hallazgo |
| --- | --- |
| ¿Resolvió con lógica de negocio o solo con criterio técnico? | **Criterio técnico.** Eligió la rama entrante «porque el nombre indica un cambio planeado para 2027 y es el más reciente». Descartó los 31 días sin decirlo, porque se quedó con la línea entera de la otra rama, y aplicó hoy (noviembre de 2026) un precio que su propia rama decía que era para 2027. |
| ¿Qué hizo bien? | Pidió confirmar con quien define los planes antes de cerrar, y recordó buscar otras referencias a 75.000 y a 31 días. |

**Corrección.** La duración sale de la regla de negocio, no de la rama más nueva: HU-02 y RN-03 fijan el plan Mensual en 30 días, y 31 le regalaría a cada socio unos 12 días al año. El precio no se cambia en el código: según RN-08 y HU-04, lo cambia el administrador en la gestión de planes, con fecha de vigencia. Se dejó `("Mensual", 30, 75000)` y el precio de 2027 quedó pendiente de HU-04 (DT-24).
