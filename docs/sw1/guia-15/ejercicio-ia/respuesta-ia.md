Aquí tienes un workflow básico de GitHub Actions para FitManage. Se ejecuta en cada push y pull request: primero corre las pruebas con pytest contra un PostgreSQL de servicio, y solo si pasan y el push es a `main`, construye y sube la imagen Docker a Docker Hub.

Guárdalo en `.github/workflows/ci.yml` de la raíz del repositorio:

```yaml
name: CI FitManage

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    name: Pruebas (Django 5.2 + PostgreSQL)
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: fitmanage_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      DJANGO_SECRET_KEY: ci-clave-no-secreta
      DJANGO_DEBUG: "False"
      DB_NAME: fitmanage_test
      DB_USER: postgres
      DB_PASSWORD: postgres
      DB_HOST: localhost
      DB_PORT: 5432

    steps:
      - name: Clonar repositorio
        uses: actions/checkout@v4

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Instalar dependencias
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-django

      - name: Verificar migraciones pendientes
        run: python manage.py makemigrations --check --dry-run

      - name: Aplicar migraciones
        run: python manage.py migrate

      - name: Ejecutar pruebas con pytest
        run: pytest

  docker:
    name: Construir y subir imagen a Docker Hub
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    steps:
      - name: Clonar repositorio
        uses: actions/checkout@v4

      - name: Configurar Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Iniciar sesión en Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Generar etiquetas y metadatos
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ secrets.DOCKERHUB_USERNAME }}/fitmanage
          tags: |
            type=raw,value=latest
            type=sha

      - name: Construir y subir imagen
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

Antes de que funcione, ten en cuenta lo siguiente:

1. **Secretos del repositorio.** En GitHub ve a *Settings > Secrets and variables > Actions* y crea `DOCKERHUB_USERNAME` (tu usuario de Docker Hub) y `DOCKERHUB_TOKEN` (un Access Token generado en Docker Hub, no tu contraseña).
2. **Configuración de Django.** El workflow asume que `settings.py` lee `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` y las variables `DB_*` desde el entorno. Si tu proyecto usa otros nombres, ajústalos en la sección `env` del job `test`.
3. **pytest-django.** Para que pytest encuentre los settings, agrega a `pytest.ini` (o `pyproject.toml`) algo como `DJANGO_SETTINGS_MODULE = tu_proyecto.settings`. Si ya lo tienes, no hace falta nada más.
4. **requirements.txt.** Debe estar en la raíz y contener `Django==5.2.*` y `psycopg[binary]` (o `psycopg2-binary`). Si pytest ya está ahí, puedes quitar la línea `pip install pytest pytest-django`.
5. **Dockerfile.** Debe existir en la raíz del repositorio, porque `build-push-action` lo usa por defecto.
6. **Versión de Python.** Django 5.2 soporta Python 3.10 a 3.13; el archivo usa 3.12.
