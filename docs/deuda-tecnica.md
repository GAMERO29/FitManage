# Inventario de deuda técnica (FPI-17)

Cada refactorización futura debe citar en su Pull Request el ítem que paga (por ejemplo, `Paga DT-07`). Los ítems DT-01 a DT-03 vienen de la FPI-12; DT-04 a DT-10 se encontraron en la auditoría de la línea base LB-1.

| ID | Ítem de deuda | Categoría | Ubicación | Impacto en calidad | Cuadrante de Fowler | Plan de pago e hito |
| --- | --- | --- | --- | --- | --- | --- |
| DT-01 | La verificación del comprobante duplicado (RN-06) y el guardado del pago no son atómicos. | Diseño (concurrencia de datos) | `dominio/servicios.py`, líneas 91–100 | Alto: dos recepcionistas pueden registrar la misma referencia y duplicar un ingreso. | Deliberada y prudente | Semana 4: índice único parcial en PostgreSQL sobre la referencia de los pagos vigentes; el repositorio traduce el error de integridad a `ReferenciaDuplicada`; prueba con dos registros concurrentes. |
| DT-02 | Todas las pruebas usan repositorios en memoria; no hay ninguna prueba contra la base de datos. | Pruebas | `tests/dobles.py` | Alto: no está verificado el comportamiento real con PostgreSQL (tipos `NUMERIC`, unicidad, zona horaria). | Deliberada y prudente | Semanas 4–5: repositorios con Django ORM y la misma batería como pruebas de contrato, ejecutada en GitHub Actions con un servicio PostgreSQL 16. |
| DT-03 | `Socio` no valida el teléfono (10 dígitos) ni el formato del número de documento; el prototipo valida el teléfono solo al pintar la tabla. | Diseño | `dominio/modelos.py`, líneas 50–65 · `prototipo/FitManage_Prototipo.html`, línea 163 | Medio: socios con datos inválidos y recordatorios de WhatsApp (RF-06) a números inexistentes. | Deliberada y prudente | Semana 2: objetos de valor `Telefono` y `NumeroDocumento` validados en el constructor, con sus pruebas. |
| DT-04 | El prototipo reimplementa reglas del dominio en JavaScript: el vencimiento (RN-03), una fecha de inicio fija para la renovación (RN-04), los estados escritos a mano (RN-05) y un comprobante duplicado fijo (RN-06). | Diseño / arquitectónica | `prototipo/FitManage_Prototipo.html`, líneas 104, 215, 216 y 362 | Alto: dos fuentes de verdad para las mismas reglas; si el prototipo se usa como base, la interfaz calculará fechas distintas al dominio. | Deliberada e imprudente | Semanas 5–6: la interfaz Django no calcula nada y consume los servicios del dominio y `/api/v1/estados/`. El prototipo queda congelado como referencia de experiencia de usuario, no como código base. |
| DT-05 | El control de acceso por rol existe solo en el navegador y el prototipo trae una contraseña de demostración en el código. | Seguridad | `prototipo/FitManage_Prototipo.html`, líneas 116, 148 y 316 | Alto: cualquier persona puede saltarse la restricción editando el navegador; incumple RNF-05 si se reutiliza. | Deliberada e imprudente | Semana 5: decorador `@requiere_rol` en el servidor con pruebas de respuesta 403 (CP-09a); ninguna credencial en el repositorio; secretos como variables de entorno del PaaS. |
| DT-06 | El manejador de clics del prototipo concentra 13 acciones en una sola función con complejidad ciclomática 23; además hay dos manejadores `submit` distintos. | Código | `prototipo/FitManage_Prototipo.html`, líneas 335, 348–372 y 373 | Medio: harían falta al menos 23 casos de prueba para cubrir esa función. | Inadvertida e imprudente | Se paga al retirar el prototipo (DT-04). Para la aplicación real, el flujo `Calidad` rechaza cualquier bloque con complejidad mayor que 10. |
| DT-07 | El puerto `Reloj` devuelve fechas sin zona horaria, `Pago` acepta `datetime` sin zona y no existe `RelojBogota`; ruff reporta 13 avisos DTZ001. | Diseño | `dominio/puertos.py`, líneas 33–39 · `dominio/modelos.py`, línea 118 | Alto: reaparecería el defecto de la revisión técnica formal: después de las 7:00 p. m. el servidor en UTC ya vive en el día siguiente y mostraría «Vencido» a socios que vencen hoy. | Inadvertida y prudente | Semana 2: `RelojBogota` con `zoneinfo("America/Bogota")`, invariante en `Pago` que exige zona horaria y regla DTZ activada en ruff. |
| DT-08 | Hasta esta semana el código vivía en un archivo `.zip` sin control de versiones; el archivo se perdió y el núcleo se reconstruyó a partir de la FPI-12. No había integración continua ni un entorno reproducible. | Infraestructura | Repositorio completo | Alto: pérdida de historia y de evidencia; imposible reproducir una versión anterior. | Inadvertida e imprudente | Pagada en parte en esta ficha: repositorio en GitHub, etiqueta `LB-1` y flujo `Calidad`. Semana 3: `Dockerfile` y `docker-compose` con PostgreSQL 16. |
| DT-09 | Dos líneas del dominio no tienen prueba: el caso sin mora de `dias_de_mora` y el documento vacío en `Socio`. | Pruebas | `dominio/calculadora.py`, línea 36 · `dominio/modelos.py`, línea 61 | Bajo: son caminos simples, pero hoy un cambio en ellos pasaría sin detectarse. | Inadvertida y prudente | Semana 2: dos pruebas nuevas; el flujo `Calidad` exige cobertura mínima de 95 %. |
| DT-10 | El texto oficial de autorización de tratamiento de datos no está redactado; el prototipo muestra un marcador. | Seguridad (cumplimiento legal) | `prototipo/FitManage_Prototipo.html`, línea 255 | Alto antes de usar datos reales: sin el texto aprobado, la autorización que exige la Ley 1581 de 2012 no es válida. | Deliberada y prudente | Antes del piloto con datos reales: redactar con el dueño del gimnasio el aviso de privacidad y la autorización, versionarlos en `docs/legal/` y guardar con cada socio la versión que aceptó. |

## Ítems nuevos

| ID | Ítem de deuda | Categoría | Ubicación | Impacto en calidad | Cuadrante de Fowler | Plan de pago e hito |
| --- | --- | --- | --- | --- | --- | --- |
| DT-11 | Los usuarios se guardan desde `PagoRepositorioORM` (tabla `usuarios` provisional) porque aún no existe el módulo de cuentas. | Diseño | `infraestructura/persistencia/repositorios.py`, `_guardar_usuario` | Medio: el repositorio de pagos tiene una responsabilidad que no le corresponde. | Deliberada y prudente | Semana 5: módulo `cuentas` sobre el usuario de Django; el repositorio de pagos solo referencia el id. |

## Resumen

| Categoría | Ítems | Impacto alto |
| --- | --- | --- |
| Código | DT-06 | 0 |
| Diseño / arquitectónica | DT-01, DT-03, DT-04, DT-07 | 3 |
| Pruebas | DT-02, DT-09 | 1 |
| Seguridad e infraestructura | DT-05, DT-08, DT-10 | 3 |

## Pagos realizados

| ID | Semana | Cómo se pagó | Commit de integración |
| --- | --- | --- | --- |
| DT-07 | 2 | `infraestructura/reloj.py` (`RelojBogota`), fechas obligatoriamente con zona horaria en `Socio` y `Pago`, regla DTZ de ruff activa y escenario QA-03 automatizado en `tests/test_reloj.py`. | `a205da0` |
| DT-09 | 2 | Pruebas para el caso sin mora, el documento vacío y el reloj real; cobertura de líneas y ramas del 100 %. | `be87164` |
| DT-03 | 2 | Objetos de valor `Telefono` y `NumeroDocumento`, validados al crear un `Socio`, con 11 casos de prueba nuevos. | `f9d271f` |
| DT-08 | 3 | `Dockerfile` (Python 3.12, usuario sin privilegios) y `docker-compose.yml` con PostgreSQL 16; la contraseña se lee de `.env`, que no se sube. El flujo `Calidad` agrega el trabajo `contenedores`, que construye la imagen, corre las pruebas dentro y comprueba que la app alcanza la base de datos. | `781ad56` |
| DT-02 | 4 | Adaptadores `SocioRepositorioORM`, `PlanRepositorioORM` y `PagoRepositorioORM`; las mismas pruebas de contrato corren contra los dobles en memoria y contra Django ORM, con SQLite en el trabajo de pruebas y con PostgreSQL 16 en el trabajo de contenedores. | PR #1 (`e59244c`) |
| DT-01 | 4 | Índice único parcial `referencia_vigente_unica` en la tabla `pagos`; el adaptador traduce la violación a `ReferenciaDuplicada`. QA-05 corre 100 pares de registros simultáneos contra PostgreSQL 16 y en los 100 la base rechaza el segundo. | PR #1 (`e59244c`) |
