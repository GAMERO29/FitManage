# Entorno reproducible de FitManage (paga DT-08): la misma versión de Python que el flujo Calidad.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt

COPY . .

RUN useradd --create-home fitmanage && chown -R fitmanage /app
USER fitmanage

CMD ["pytest"]
