-- Guía II-05 · Señal operativa: pagos que cambiaron después de la migración 0003 sin su evento.
-- Si devuelve filas, alguna versión sin auditoría escribió en la base (por ejemplo, tras volver a
-- una imagen anterior) o hay un defecto. Uso: psql "$DATABASE_URL" -f coherencia_auditoria.sql
WITH desde AS (
  SELECT applied AS momento FROM django_migrations
  WHERE app = 'persistencia' AND name = '0003_auditoria_y_coherencia_de_anulacion'
)
SELECT 'registrado sin evento' AS problema, p.id, p.registrado_en
FROM pagos p, desde
WHERE p.registrado_en >= desde.momento
  AND NOT EXISTS (SELECT 1 FROM auditoria a WHERE a.entidad_id = p.id
                  AND a.tipo IN ('PAGO_REGISTRADO', 'PLAN_CAMBIADO'))
UNION ALL
SELECT 'anulado sin evento', p.id, p.fecha_anulacion
FROM pagos p, desde
WHERE p.estado = 'ANULADO' AND p.fecha_anulacion >= desde.momento
  AND NOT EXISTS (SELECT 1 FROM auditoria a WHERE
                    (a.tipo = 'PAGO_ANULADO' AND a.entidad_id = p.id)
                    OR (a.tipo = 'PLAN_CAMBIADO' AND a.detalle ->> 'pagoAnulado' = p.id::text))
ORDER BY 3;
