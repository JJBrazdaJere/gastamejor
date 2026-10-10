-- 002_constraints_rollback.sql
-- Revierte 002_constraints.sql.

BEGIN;

ALTER TABLE detalle_ventas DROP CONSTRAINT IF EXISTS detalle_ventas_cantidad_positiva;
ALTER TABLE productos      DROP CONSTRAINT IF EXISTS productos_precio_positivo;
ALTER TABLE productos      DROP CONSTRAINT IF EXISTS productos_stock_no_negativo;
ALTER TABLE ventas         ALTER COLUMN fecha DROP DEFAULT;

COMMIT;
