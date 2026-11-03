# syntax=docker/dockerfile:1
# Imagen de FitManage en tres etapas (Guía 10, FPI-26, ADR N.° 10).
#
#   construccion  instala las dependencias de producción en un entorno virtual
#   pruebas       la etapa anterior + herramientas de desarrollo + todo el repositorio; corre pytest
#   venv-produccion  copia del entorno virtual sin pip (pip no hace falta para servir; ADR N.° 12)
#   produccion    solo Python, el entorno virtual y el código de la aplicación; usuario sin privilegios
#
#   docker build --target produccion -t fitmanage .     # la que se despliega (por defecto)
#   docker build --target pruebas    -t fitmanage:pruebas .

# Fijada por digest: la etiqueta puede cambiar con un parche; el digest no. Dependabot la actualiza.
ARG PYTHON_IMAGEN=python:3.12-slim-trixie@sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30

# ---------- 1. construccion ----------
# nosemgrep: dockerfile.best-practice.missing-image-version (versión y digest en PYTHON_IMAGEN)
FROM ${PYTHON_IMAGEN} AS construccion
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
# Primero solo la lista de dependencias: mientras requirements.txt no cambie, Docker reutiliza
# esta capa y no vuelve a descargar nada aunque cambie el código.
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# ---------- 2. pruebas (no se publica) ----------
# nosemgrep: dockerfile.best-practice.missing-image-version (versión y digest en PYTHON_IMAGEN)
FROM construccion AS pruebas
COPY requirements-dev.txt /tmp/requirements-dev.txt
# requirements-dev.txt incluye -r requirements.txt, que ya está instalado en la etapa anterior.
RUN pip install -r /tmp/requirements-dev.txt \
    && useradd --system --uid 10001 --create-home fitmanage
WORKDIR /app
COPY --chown=10001 . .
USER 10001
ENV PYTHONUNBUFFERED=1
CMD ["pytest", "-p", "no:cacheprovider"]

# ---------- 3. venv-produccion (no se publica) ----------
# pip solo sirve para instalar, y es una de las piezas con más CVE de la imagen. Aquí se quita del
# entorno virtual que va a producción; la etapa pruebas conserva el suyo.
# nosemgrep: dockerfile.best-practice.missing-image-version (versión y digest en PYTHON_IMAGEN)
FROM construccion AS venv-produccion
RUN python -m pip uninstall --yes --root-user-action=ignore pip

# ---------- 4. produccion (la que se publica en GHCR) ----------
# nosemgrep: dockerfile.best-practice.missing-image-version (versión y digest en PYTHON_IMAGEN)
FROM ${PYTHON_IMAGEN} AS produccion
# El pipeline pasa el SHA del commit; /api/v1/salud lo publica (ADR N.° 11).
ARG VERSION=desarrollo
# gunicorn escucha en 0.0.0.0:$PORT cuando PORT existe; Render la cambia por la suya.
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FITMANAGE_VERSION=$VERSION \
    PORT=8000 \
    HOME=/tmp
# Endurecimiento del sistema base (ADR N.° 12):
#   - fuera el pip de Python del sistema: en ejecución nadie instala paquetes;
#   - ningún ejecutable con setuid/setgid (mount, umount, su, passwd, chfn...): aunque alguien tome
#     el proceso, no tiene un binario de root con qué escalar. Mitiga los CVE de util-linux.
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin fitmanage \
    && python -m pip uninstall --yes --root-user-action=ignore pip \
    && find / -xdev -perm /6000 -type f -exec chmod a-s {} +
WORKDIR /app
COPY --from=venv-produccion /opt/venv /opt/venv
# Solo el código que corre en el servidor. Queda de root y en solo lectura para el proceso:
# si alguien explota la aplicación, no puede reescribirla.
COPY manage.py ./
COPY config/ config/
COPY dominio/ dominio/
COPY aplicacion/ aplicacion/
COPY infraestructura/ infraestructura/
COPY docs/api/openapi.yaml docs/api/openapi.yaml
COPY --chmod=755 docker/arrancar.sh /app/arrancar.sh
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f\"http://127.0.0.1:{os.environ['PORT']}/api/v1/salud\", timeout=2)"]
# Un proceso con 4 hilos: las métricas viven en memoria del proceso y con dos workers cada lectura
# de /metrics mostraría solo la mitad del tráfico. Sin --access-logfile: escribía la URL completa,
# con la cédula, en los logs de Render; ahora cada petición deja una línea JSON sin datos personales.
CMD ["gunicorn", "config.wsgi", "--workers", "1", "--threads", "4"]
