# syntax=docker/dockerfile:1
# Imagen de FitManage en tres etapas (Guía 10, FPI-26, ADR N.° 10).
#
#   construccion  instala las dependencias de producción en un entorno virtual
#   pruebas       la etapa anterior + herramientas de desarrollo + todo el repositorio; corre pytest
#   produccion    solo Python, el entorno virtual y el código de la aplicación; usuario sin privilegios
#
#   docker build --target produccion -t fitmanage .     # la que se despliega (por defecto)
#   docker build --target pruebas    -t fitmanage:pruebas .

ARG PYTHON_IMAGEN=python:3.12-slim-trixie

# ---------- 1. construccion ----------
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

# ---------- 3. produccion (la que se publica en GHCR) ----------
FROM ${PYTHON_IMAGEN} AS produccion
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin fitmanage
WORKDIR /app
COPY --from=construccion /opt/venv /opt/venv
# Solo el código que corre en el servidor. Queda de root y en solo lectura para el proceso:
# si alguien explota la aplicación, no puede reescribirla.
COPY manage.py ./
COPY config/ config/
COPY dominio/ dominio/
COPY aplicacion/ aplicacion/
COPY infraestructura/ infraestructura/
COPY docs/api/openapi.yaml docs/api/openapi.yaml
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/salud', timeout=2)"]
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-"]
