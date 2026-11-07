# Ejercicio 5 · Una IA audita la bitácora de IA del programa, y yo audito a la IA auditora

- **Asistente:** Claude Haiku (`claude-haiku-5-5`), sin herramientas de búsqueda ni acceso al repositorio.
- **Prompt:** [`prompt.txt`](prompt.txt). Le pasé las dos tablas de la bitácora (Software I y Software II), sin los totales, sin los tres hallazgos que elegí yo y sin la sección «Lo que la bitácora no esconde». Así podía comprobar si llegaba sola a las mismas conclusiones.
- **Respuesta:** [`respuesta-ia.md`](respuesta-ia.md), sin editar.

## Qué hizo bien

- **Reconoció todos los errores que había detectado yo.** Listó las 13 fichas con alucinación y contó bien: 15 afirmaciones falsas en 13 de 27 fichas, sin que le diera los totales.
- **No se inventó alucinaciones nuevas.** Cada punto de su lista está en la bitácora.
- **No fue complaciente con la IA.** Fue directa con las afirmaciones falsas de seguridad (FPI-17, FPI-22, FPI-29) y no las suavizó.

## Qué hizo mal

Su sesgo no fue la autoevaluación positiva que advierte la guía. Fue el contrario: **convirtió lo que la IA propuso en cosas que yo hice.** Contrasté cada afirmación con el repositorio:

| Lo que dijo la IA auditora | Lo que muestra el repositorio | Veredicto |
| --- | --- | --- |
| «Si las credenciales de Docker Hub y el deploy hook de Render estuvieron en el repositorio público, rótalas ya.» | Esos valores los inventé para la prueba, y así lo dice `docs/guia-11-sw2/ejercicio-ia/prompt-y-respuesta.md`. El hook real vive en un secreto del environment `produccion` y nunca pasó por una conversación. El check `secretos` revisa cada PR. | **Falso.** Lo trató como una filtración real. |
| «Pediste refactorizaciones grandes que rompieron flujos que ya funcionaban (FPI-31).» | La refactorización de la IA se aplicó en una copia aparte del repositorio y nunca entró a `main`. Los pagos de producción no se tocaron. | **Falso.** |
| «Adoptaste afirmaciones de seguridad y de "listo para producción" antes de verificarlas (FPI-17, FPI-22, FPI-29).» | En las tres fichas, la afirmación se refutó con una prueba antes de escribir la corrección (`test_auditoria_respuesta_ia.py`, `test_openapi.py`, `revertir_hash.py`). | **Falso.** |
| «Aceptaste sobrediseño en varias fichas (FPI-19, FPI-21, FPI-10).» | Las tres propuestas se rechazaron: ADR N.° 03, ADR N.° 05 y un diagrama de 2 elementos en lugar de 14. | **Falso.** |
| «El reporte que FPI-28 publica en GitHub Pages conviene que sea privado.» | Nunca se publicó: los SARIF van al panel Security, que es privado. | Recomendación sobre algo que no existe. |
| Ordenó FPI-17 como la alucinación más crítica. | Es discutible, pero defendible. Yo pongo primero la FPI-29, porque la frase falsa («la cédula no se guarda») tranquiliza justo a quien debía preocuparse, y el dato es personal. | Diferencia de criterio. |

**Lo que no vio.** No notó que en la tabla de Software I no hay una columna de evidencia, ni que esas auditorías fueron de lectura y no se ejecutaron. Tampoco dijo nada del conflicto de interés más obvio: me pidieron que una IA de Anthropic audite el trabajo de otra IA de Anthropic. Ninguna de las dos cosas estaba escrita en las tablas, pero un auditor humano habría preguntado por las dos.

## Parte del error era mío

Los cinco «falsos» tienen la misma raíz: la tabla decía, por ejemplo, «contraseña de Docker Hub y deploy hook de Render en claro, en un repositorio público», sin aclarar que **la IA propuso** eso y que los valores eran inventados. Una lectura apurada lo entiende como un hecho. Corregí la bitácora: ahora tiene un párrafo que separa lo propuesto de lo hecho, y cada fila de riesgo dice «propuso» o «se aplicó en una copia aparte». Una bitácora forense tiene que entenderse bien también con una lectura apurada.

## Evaluación final

- **Calificación que me dio:** 4 de 5.
- **Mi evaluación de esa calificación:** el número es razonable, pero las razones no. Los cuatro puntos que me quitó se basan en hechos que no ocurrieron. Si una IA da un número correcto por razones equivocadas, el número no vale nada.
- **Lección:** un auditor automático puede pecar por exceso de severidad, no solo por complacencia, y las dos cosas son alucinaciones. La regla fue la misma de todo el programa: ninguna afirmación se acepta, ni a favor ni en contra, hasta contrastarla con el repositorio.
