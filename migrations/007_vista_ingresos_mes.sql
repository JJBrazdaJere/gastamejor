-- 007_vista_ingresos_mes.sql
-- Vista de apoyo: total y cantidad de ingresos por usuario y mes.
-- La usa el backend para los resumenes mensuales (y queda comoda para psql).

BEGIN;

CREATE VIEW ingresos_mes AS
SELECT
    i.cliente_id,
    to_char(date_trunc('month', i.fecha), 'YYYY-MM') AS mes,
    SUM(i.monto)   AS total,
    COUNT(*)       AS cantidad
FROM ingresos i
GROUP BY i.cliente_id, date_trunc('month', i.fecha);

COMMIT;
