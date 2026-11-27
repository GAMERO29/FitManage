# Software III, Guía 14 (ADR N.° 20, DEF-03): TRUNCATE tampoco vacía la auditoría.
#
# TRUNCATE no dispara los disparadores de fila de la migración 0003, así que hace falta uno de
# sentencia. La única excepción es una sesión que declare fitmanage.permitir_vaciado = 'si'; eso
# solo lo hace tests/conftest.py, porque pytest-django vacía las tablas con TRUNCATE entre las
# pruebas que usan transacciones reales. La aplicación nunca lo declara.
# SQLite no tiene TRUNCATE: su DELETE sin condición ya lo frena el disparador de la 0003.
from django.db import migrations

POSTGRES_CREAR = """
CREATE FUNCTION auditoria_sin_vaciado() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF current_setting('fitmanage.permitir_vaciado', true) IS DISTINCT FROM 'si' THEN
        RAISE EXCEPTION 'La auditoría no se puede vaciar: TRUNCATE no está permitido';
    END IF;
    RETURN NULL;
END $$;
CREATE TRIGGER auditoria_sin_truncate BEFORE TRUNCATE ON auditoria
    FOR EACH STATEMENT EXECUTE FUNCTION auditoria_sin_vaciado();
"""
POSTGRES_BORRAR = """
DROP TRIGGER IF EXISTS auditoria_sin_truncate ON auditoria;
DROP FUNCTION IF EXISTS auditoria_sin_vaciado();
"""


def crear(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(POSTGRES_CREAR, params=None)


def borrar(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(POSTGRES_BORRAR, params=None)


class Migration(migrations.Migration):
    dependencies = [("persistencia", "0003_auditoria_y_coherencia_de_anulacion")]

    operations = [migrations.RunPython(crear, borrar)]
