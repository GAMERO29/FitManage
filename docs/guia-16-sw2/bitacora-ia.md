# Bitácora forense de auditoría de IA · FitManage (FPI-01 a FPI-31)

Guía 16 (FPI-32). Consolida los ejercicios de IA de las fichas del programa. Cada fila remite a su evidencia, y cada número de este archivo sale de contar las filas de abajo, no de un estimado.

## Alcance y método

- **Fichas cubiertas: las 31.** FPI-01 a FPI-12 (guías de Software I, usadas como guía del proyecto; documentos del proyecto), FPI-13 a FPI-16 (guías de Software I, diligenciadas el 6/11/2026, carpetas `docs/sw1/guia-XX/ejercicio-ia/`) y FPI-17 a FPI-31 (guías de Ingeniería de Software II, carpetas `docs/guia-XX-sw2/ejercicio-ia/`).
- **Herramienta:** Claude (Anthropic) en todas las fichas. En la FPI-13 a FPI-16, la FPI-28 y la FPI-31 fue Claude Haiku.
- **Cómo se auditó.** En las FPI-01 a FPI-12 la auditoría fue de lectura: se comparó la respuesta con el enunciado y con las fuentes. En Software II, desde la FPI-17, cada afirmación se ejecutó: pruebas que pasan solo si el defecto existe, linters (ruff, bandit, actionlint, Redocly, Spectral), el código de la IA corrido en CI o en una copia aparte, y sondas contra la API real.
- **Datos enviados a la IA:** ninguna ficha envió datos de socios. Se mandó código ficticio de la guía, el código o el contrato de FitManage sin datos, o una descripción genérica («un gimnasio pequeño»).

**Lo que propuso la IA no es lo que se hizo.** Las columnas de riesgo describen lo que la IA *propuso*. Ninguna de esas propuestas se adoptó: el código de la IA se corrió en una copia aparte, en un PR de demostración o como archivo `.txt` de evidencia. Los secretos que aparecen en sus respuestas (FPI-25 y FPI-27) los inventé para la prueba, y así lo dice cada `prompt-y-respuesta.md`. Ningún secreto real pasó por una conversación ni quedó en el repositorio; el check `secretos` lo revisa en cada PR.

**Qué cuenta como alucinación.** Una afirmación falsa que la IA presenta como un hecho y que se puede comprobar: un dato histórico, una ruta o una propiedad que no existe, un costo, una garantía de seguridad o un resultado. Una mala decisión de diseño (sobrediseño, un requisito vago, una práctica insegura) **no** cuenta como alucinación: se cuenta aparte, porque se discute, no se refuta.

## Guías de Software I (FPI-01 a FPI-16)

| Ficha | Qué se pidió | Alucinaciones (afirmaciones falsas) | Otros hallazgos | Dependencias o herramientas rechazadas |
| --- | --- | --- | --- | --- |
| FPI-01 | Explicar la falla del Therac-25 y proponer código | **1**: culpó a la «interfaz gráfica»; la terminal era de texto y la causa fue una condición de carrera. | El código confiaba en una variable en memoria, no en el sensor. No dijo nada de licencias. | — |
| FPI-02 | Metodología para una app de domicilios | 0 | Recomendó Scrum «por popular», sin criterios. | — |
| FPI-03 | Tareas técnicas de una historia simple | 0 | Sobrediseño; criterios de aceptación subjetivos («muy rápido», «amigable»). | 4: clúster en AWS, MongoDB distribuido, microservicio en Node.js, Kafka. |
| FPI-04 | Guion de entrevista para una panadería | 0 | Preguntas genéricas, solo para la dueña; asumió pagos con tarjeta. | — |
| FPI-05 | Un RF y un RNF para un restaurante | 0 | Ninguno verificable; omitió la facturación electrónica de la DIAN. | — |
| FPI-06 | Historia de usuario de inicio de sesión | 0 | Escrita «como desarrollador»; Gherkin cosmético. | — |
| FPI-07 | Priorización del backlog de FitManage | 0 | **Riesgo:** propuso quitar el inicio de sesión y las copias de seguridad del MVP, sin advertir el riesgo. | — |
| FPI-08 | Análisis de impacto de pagos con criptomonedas | **1**: «impacto bajo, 2 a 3 días»; el análisis propio dio de 12 a 15 días-persona. | Solo miró el código: ni pruebas ni documentación. | — |
| FPI-09 | Modelo de dominio de una biblioteca | **1**: inventó cuatro entidades sin sustento en el enunciado (Editorial, Sala de lectura, Evento cultural, Reserva). | Cardinalidades erradas (Usuario–Préstamo 1:1); no separó Libro de Ejemplar. | — |
| FPI-10 | Diagrama de clases detallado | 0 | BDUF: 14 clases y más de 60 getters y setters para un formulario. | — |
| FPI-11 | Refactorizar con SOLID | 0 | 13 elementos, abstracciones de una sola implementación. | — |
| FPI-12 | Refactorizar código con malos nombres | 0 | Solo reorganizó: `paso1`, `paso2`, números mágicos intactos. | — |
| FPI-13 | Resolver un conflicto de mezcla real | 0 | Eligió la rama «más reciente» por su nombre, sin mirar las reglas del negocio, y aplicó desde hoy un precio previsto para 2027. | — |
| FPI-14 | Pruebas unitarias de `CalculadoraMembresia` | **1**: importó un módulo que no existe (`dominio.calculos`); la suite no arrancaba. | Con el import corregido, sus 23 pruebas detectaron los 4 mutantes. Usó un doble simple, sin mocks innecesarios. | — |
| FPI-15 | YAML de CI | 0 | **Riesgo:** con variables que el proyecto no lee, el job de «PostgreSQL» habría probado SQLite. Una contraseña y una clave de prueba en claro. | — |
| FPI-16 | Autoevaluación del equipo | 0 | Plantilla genérica con 52 marcadores; supuso un equipo de varias personas en un proyecto individual. | — |

## Guías de Software II (FPI-17 a FPI-31)

| Ficha | Qué se pidió | Alucinaciones (afirmaciones falsas) | Riesgo de seguridad o privacidad | Dependencias o herramientas rechazadas | Evidencia |
| --- | --- | --- | --- | --- | --- |
| FPI-17 | Refactorizar código legado con SOLID | **2**: «la API key ya no queda expuesta» (seguía como valor por defecto) y «listo para producción» (`Decimal * float` rompe cualquier venta real). | Secreto en el código. | 2: psycopg2 y requests (la versión corregida no agrega dependencias). Licencias revisadas: LGPL y Apache-2.0, ninguna restrictiva. | `guia-01-sw2/ejercicio-ia/test_auditoria_respuesta_ia.py` (5 pruebas) |
| FPI-18 | Tres escenarios de calidad | 0 | — | — | `guia-02-sw2/ejercicio-ia/` |
| FPI-19 | Arquitectura sin contexto | 0 (sobrediseño, no dato falso) | — | 8: microservicios con base por servicio, Kong o API Gateway, Kafka, Redis, EKS, React Native, ELK, Auth0 o Cognito. | ADR N.° 03 |
| FPI-20 | Refactorizar hacia hexagonal | 0 | El núcleo importaba excepciones de SQLAlchemy. | — | `guia-04-sw2/ejercicio-ia/corregido/` |
| FPI-21 | Microservicios para un negocio pequeño | **1**: «unos pocos dólares al mes»; su propio diseño cuesta unos 108 USD. | Asumió una red local siempre disponible. | 6: Lambda, cinco RDS, EventBridge, Cognito, SNS, CloudFront. | `guia-05-sw2/costos.py`, ADR N.° 05 |
| FPI-22 | OpenAPI de los endpoints reales | **1**: «incluye autenticación JWT»; el esquema existía, pero ningún endpoint lo exigía. | **Fuga de datos personales prevenida:** la consulta devolvía cédula, teléfono, dirección y fecha de nacimiento; el login devolvía la contraseña; había un `DELETE` de pagos. | — | `tests/contrato/test_openapi.py` |
| FPI-23 | Suite de integración de `POST /pagos` | 0 | Estaba escrita para usar la base de desarrollo y, al final, **borrar todos** los pagos, socios y planes. No se corrió contra esa base. Credencial fija en el código. | — | `tests/integracion/api/` |
| FPI-24 | Script de k6 | **2**: inventó el contrato (`/auth/login`, `access_token`: todo daba 404) y llamó «realista» y «estándar de la industria» a 5.000 usuarios sin pausa. | Apuntaba a un dominio de un tercero. Credenciales en el script. | — | `guia-08-sw2/ejercicio-ia/login-por-iteracion.txt` |
| FPI-25 | YAML del pipeline | **1**: la propiedad `sonar.coverage.minimum` no existe. | Propuso el token de SonarCloud en claro (inventado para la prueba); `pull_request_target` con checkout del PR (*pwn request*); Quality Gate solo informativo. | 3: acciones `@v2` retiradas y `sonarcloud-github-action@master`. | `guia-09-sw2/ejercicio-ia/actionlint-ia.txt` |
| FPI-26 | Dockerfile y compose | **1**: presentó como completo un `python:3.9` que no instala Django 5.2 (lo probó CI, corrida 41538783723). | Corre como root; `SECRET_KEY` en un `ENV` de la imagen; `admin123`; base expuesta. | 3: `python:3.9`, `postgres:latest`, compiladores en la imagen. | `guia-10-sw2/ejercicio-ia/` |
| FPI-27 | Workflow de CD | **1**: «cuando termine el curl, tu aplicación estará actualizada»; dos despliegues reales lo desmintieron. | Propuso escribir en claro, en un repositorio público, la contraseña de Docker Hub y el deploy hook (valores inventados para la prueba). | — | `guia-11-sw2/ejercicio-ia/` |
| FPI-28 | Workflow de seguridad | 0 | Publicaba el reporte de vulnerabilidades en GitHub Pages, después de advertir que era público; puertas que nunca fallan. | 4: Trivy 0.56.2, Semgrep 1.100.0 (no arrancó, corrida 41581413862), reglas remotas, GitHub Pages. | `guia-12-sw2/ejercicio-ia/` |
| FPI-29 | Instrumentar un método con datos de un cliente | **1**: «la cédula no se guarda en spans ni logs»; guardaba un hash sin clave que se revierte en 1,7 s. | **Fuga de datos personales prevenida** (Ley 1581): cédula reversible y monto del pago en la misma traza. | — | `guia-13-sw2/ejercicio-ia/revertir_hash.py` |
| FPI-30 | Runbook | **1**: comandos y rutas que no existen en este entorno (`fitmanage.wsgi`, `/api/health/`, la Shell del plan gratuito, recuperación a un punto en el tiempo). | Supuso un equipo de soporte que no existe. | — | `guia-14-sw2/ejercicio-ia/` |
| FPI-31 | Ingeniería inversa de `registrar_pago` | **1**: «las entradas inválidas producen 500»; el contrato las rechaza con 400. | Su refactorización, aplicada en una copia aparte, rompía los 14 flujos de pago, y su migración borraba la tabla de idempotencia. No se adoptó. | — | `guia-15-sw2/ejercicio-ia/` |

## Totales (31 fichas)

| Indicador | Software I | Software II | Total |
| --- | --- | --- | --- |
| Fichas con ejercicio de IA auditado | 16 | 15 | **31** |
| Alucinaciones detectadas (afirmaciones falsas comprobadas) | 4 | 12 | **16** |
| Fichas con al menos una alucinación | 4 | 10 | **14** |
| Dependencias o herramientas propuestas y rechazadas | 4 | 26 | **30** |
| Licencias rechazadas por ser restrictivas | 0 | 0 | **0** |
| Propuestas con secretos o credenciales en claro | 1 (FPI-15) | 6 (FPI-17, 23, 24, 25, 26, 27) | **7** |
| Fugas de datos personales propuestas y prevenidas | 0 | 2 (FPI-22, FPI-29) | **2** |
| Fichas en las que la IA recibió datos reales de socios | 0 | 0 | **0** |

**Sobre las licencias.** Ninguna sugerencia de la IA trajo una licencia restrictiva: las que propuso eran MIT, BSD, Apache-2.0 o LGPL usada como librería. Hasta la Guía 16 ninguna puerta revisaba las licencias del proyecto real. Desde esta guía, el check `sca-dependencias` instala las dependencias de ejecución y falla si aparece una licencia fuera de la lista permitida. Hoy hay 49 paquetes: el único LGPL es psycopg, y el único MPL, certifi.

## Los tres hallazgos éticos más significativos

1. **FPI-29 · «La cédula no se guarda».** La IA lo afirmó en su explicación y dejó en cada traza un hash de la cédula sin clave, junto al monto del pago. Probando los 10 millones de cédulas que empiezan por 109, se recuperó el documento en 1,7 segundos. Es la más grave del programa, porque la frase tranquiliza justo a quien debía preocuparse. Corrección: HMAC con la clave del servidor, lista blanca de campos en los logs y un workflow que falla si encuentra un documento en la telemetría.
2. **FPI-22 · Un contrato con los datos de todos los socios.** La consulta de recepción devolvía cédula, teléfono, dirección y fecha de nacimiento, y el login devolvía la contraseña. Ningún linter lo vio; se encontró leyendo el contrato con las reglas del negocio al lado. Las pruebas de `test_openapi.py` impiden que vuelva.
3. **FPI-25, FPI-27 y FPI-28 · Seguridad desactivada con buen tono.** En tres guías seguidas la IA puso un secreto en claro «para que funcione de inmediato», desactivó una puerta «para no bloquear» y publicó el reporte de vulnerabilidades en un sitio público después de advertir que era público. Lo peligroso no era un error de sintaxis, que los linters atrapan, sino la explicación razonable que lo acompañaba.

## Lo que la bitácora no esconde

- **La IA también construyó el proyecto.** Además de los ejercicios auditados, FitManage se desarrolló con un asistente de IA (Claude) en todas las guías de Software II, en modo de programación en pareja. Cada cambio entró por un PR con los nueve checks requeridos, y las decisiones de alcance, de costo y de riesgo quedaron en los ADR con su justificación. La responsabilidad de lo que se entregó es de quien firmó cada entrega.
- **En las FPI-01 a FPI-12, la auditoría fue de lectura.** Nada se ejecutó, así que es posible que alguna alucinación de esas fichas se haya pasado por alto. En Software II cada hallazgo tiene una prueba, una corrida o un archivo que lo reproduce.
- **La IA auditada y la que ayudó a corregir son de la misma familia de modelos.** Es un conflicto de interés y por eso el criterio final siempre fue una prueba o una corrida, no la opinión de otra IA. El Ejercicio 5 de la Guía 16 pone a prueba justamente eso.
