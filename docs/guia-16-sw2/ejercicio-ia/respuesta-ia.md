## Auditoría de la bitácora de IA (FitManage)

Encontré **15 afirmaciones falsas en 13 de las 27 fichas**. Ordené las alucinaciones por gravedad: primero las que llegaron al código o pusieron en riesgo datos, pagos o secretos.

### Alucinaciones más críticas

1. **FPI-17: "la API key ya no queda expuesta" y "listo para producción".** La clave seguía como valor por defecto, así que el secreto no se protegió. Además, `Decimal * float` rompe cualquier venta real.
2. **FPI-31: "las entradas inválidas producen 500".** El contrato responde 400. La refactorización basada en esa premisa rompió los 14 flujos de pago y borró la tabla de idempotencia. Es la falla de mayor impacto funcional.
3. **FPI-29: "la cédula no se guarda en spans ni logs".** Se guardaba un hash sin clave que se revertía en 1,7 s, con cédula y monto en la misma traza. Es un riesgo de privacidad bajo la Ley 1581.
4. **FPI-22: "incluye autenticación JWT".** Ningún endpoint exigía el esquema. La consulta exponía cédula, teléfono, dirección y fecha de nacimiento, y el login devolvía la contraseña.
5. **FPI-27: "cuando termine el curl, tu aplicación estará actualizada".** Dos despliegues reales lo desmintieron. Además, la contraseña de Docker Hub y el deploy hook de Render quedaron en claro en un repositorio público.
6. **FPI-26: `python:3.9` presentado como completo.** No instala Django 5.2, y la CI lo confirmó (corrida 41538783723).
7. **FPI-24: contrato inventado y carga "realista".** Los endpoints `/auth/login` y `access_token` daban 404 en todo. Además, llamó "estándar de la industria" a 5.000 usuarios sin pausa.
8. **FPI-25: la propiedad `sonar.coverage.minimum` no existe.**
9. **FPI-30: comandos y rutas inexistentes** (`fitmanage.wsgi`, `/api/health/`, la Shell del plan gratuito).
10. **FPI-21: "unos pocos dólares al mes".** Su propio diseño cuesta unos 108 USD.
11. **FPI-08: "impacto bajo, 2 a 3 días".** Su análisis propio dio 12 a 15 días-persona. Es un error de estimación que afecta la planificación.
12. **FPI-09: cuatro entidades inventadas** (Editorial, Sala de lectura, Evento cultural, Reserva) sin sustento en el enunciado.
13. **FPI-01: el Therac-25 se atribuyó a la "interfaz gráfica".** La causa fue una condición de carrera.

### Acción urgente

Si las credenciales de Docker Hub y el deploy hook de Render estuvieron en el repositorio público, **rótalas ya**, aunque las hayas quitado después. Git conserva el historial, así que deben considerarse comprometidas. Revisa también la API key de FPI-17 y el reporte de vulnerabilidades que FPI-28 publica en GitHub Pages: conviene que sea privado.

### Evaluación del uso de la IA

**Calificación: 4 de 5.**

**Fortalezas:**
- Verificaste con evidencia: pruebas automatizadas, pruebas de contrato, CI, actionlint, un script de costos y el registro de cada corrida.
- Detectaste fallas graves (fugas de datos, pagos rotos, pipeline roto) y las dejaste documentadas con sus evidencias.
- Rechazaste dependencias y herramientas innecesarias, y revisaste licencias.
- La bitácora es trazable: cada alucinación tiene su ficha, su impacto y su evidencia.

**Debilidades que explican el punto perdido:**
- Adoptaste afirmaciones de seguridad y de "listo para producción" antes de verificarlas (FPI-17, FPI-22, FPI-29). Ese es el patrón más peligroso de la bitácora.
- Pediste refactorizaciones grandes que rompieron flujos que ya funcionaban (FPI-31).
- Aceptaste sobrediseño en varias fichas (FPI-19, FPI-21, FPI-10), que tiene costo real aunque no sea una alucinación.
- Secretos en claro en un repositorio público (FPI-27), que es un error de higiene, no solo de la IA.

Para llegar a 5, cualquier afirmación de seguridad, de rendimiento o de "listo para producción" debería validarse con una prueba antes de integrarse, y las credenciales nunca deberían entrar al repositorio.
